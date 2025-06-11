# core/bulk_copy.py
from django.db import transaction
from wagtail.models import Locale, Page
from .translation_service import AITranslationService
from django.conf import settings


def duplicate_is_to_en(page_ids=None, translate_content=False) -> tuple[int, int]:
    """
    Copy Icelandic pages (except root) to the English locale.
    
    If `page_ids` is given, copy only those pages.
    If `translate_content` is True, use AI to translate the content.
    """
    src_locale = Locale.objects.get(language_code="is")
    dst_locale, _ = Locale.objects.get_or_create(language_code="en")

    pages_qs = Page.objects.filter(locale=src_locale).exclude(depth=1)
    if page_ids is not None:
        pages_qs = pages_qs.filter(id__in=page_ids)

    pages = pages_qs.specific().order_by("path")
    
    # Initialize translation service if needed
    translation_service = None
    if translate_content and hasattr(settings, 'OPENAI_API_KEY'):
        translation_service = AITranslationService()

    created = skipped = 0
    with transaction.atomic():
        for page in pages:
            if Page.objects.filter(
                translation_key=page.translation_key,
                locale=dst_locale,
            ).exists():
                skipped += 1
                continue

            new_page = page.copy_for_translation(
                locale=dst_locale,
                copy_parents=True,
                alias=False,
            )
            
            # Apply AI translation if enabled
            if translation_service:
                try:
                    # Extract translatable content
                    content = translation_service.extract_translatable_content(page)
                    
                    # Translate content
                    translated_content = translation_service.translate_content(
                        content, 
                        source_lang="is", 
                        target_lang="en",
                        page_type=page.__class__.__name__
                    )
                    
                    # Apply translations
                    translation_service.apply_translated_content(new_page, translated_content)
                    
                except Exception as e:
                    logger.error(f"Translation failed for page {page.id}: {str(e)}")
                    # Continue with original content if translation fails
            
            if page.live:
                new_page.save_revision().publish()
            created += 1

    return created, skipped