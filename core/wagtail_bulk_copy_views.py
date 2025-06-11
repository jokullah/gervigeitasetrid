from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from wagtail.models import Page, Locale
from django.conf import settings
import logging  # Add this import

logger = logging.getLogger(__name__)  # Add this line


def get_untranslated_pages(src_lang, dst_lang):
    src_locale = Locale.objects.get(language_code=src_lang)
    dst_locale, _ = Locale.objects.get_or_create(language_code=dst_lang)
    return (
        Page.objects
        .filter(locale=src_locale)
        .exclude(depth=1)
        .exclude(translation_key__in=Page.objects.filter(locale=dst_locale).values_list('translation_key', flat=True))
        .specific()
        .order_by("path")
    )


@login_required
@permission_required("wagtailadmin.access_admin", raise_exception=True)
def bulk_copy_view(request):
    # Check if AI translation is available
    ai_translation_available = hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY
    
    if request.method == "POST":
        page_ids = request.POST.getlist("pages")
        dst_lang = request.POST["dst_lang"]
        translate_content = request.POST.get("translate_content") == "on"
        
        dst_locale = Locale.objects.get(language_code=dst_lang)

        created = 0
        skipped = 0
        
        # Initialize translation service if needed
        translation_service = None
        if translate_content and ai_translation_available:
            from .translation_service import AITranslationService
            translation_service = AITranslationService()
        
        for page_id in page_ids:
            page = Page.objects.get(id=page_id).specific
            if Page.objects.filter(translation_key=page.translation_key, locale=dst_locale).exists():
                skipped += 1
                continue
            
            try:
                new_page = page.copy_for_translation(
                    locale=dst_locale, 
                    copy_parents=True, 
                    alias=False
                )

                # Apply AI translation if enabled
                if translation_service:
                    try:
                        content = translation_service.extract_translatable_content(page)
                        translated_content = translation_service.translate_content(
                            content, 
                            source_lang=page.locale.language_code, 
                            target_lang=dst_lang,
                            page_type=page.__class__.__name__
                        )
                        translation_service.apply_translated_content(new_page, translated_content)
                    except Exception as e:
                        logger.error(f"Translation failed for page {page.id}: {str(e)}")

                # Try to save and publish
                if page.live:
                    new_page.save_revision().publish()
                else:
                    new_page.save()
                
                created += 1
                
            except Exception as e:
                logger.error(f"Failed to copy page {page.id}: {str(e)}")
                skipped += 1
                continue

        success_msg = f"✅ {created} copied, {skipped} skipped."
        if translate_content and created > 0:
            success_msg += " 🤖 AI translation applied."
        
        messages.success(request, success_msg)
        return redirect(reverse("wagtailadmin_home"))

    return render(request, "bulk_copy/chooser.html", {
        "is_to_en": get_untranslated_pages("is", "en"),
        "en_to_is": get_untranslated_pages("en", "is"),
        "ai_translation_available": ai_translation_available,
    })
