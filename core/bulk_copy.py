# core/bulk_copy.py
from django.db import transaction
from wagtail.models import Locale, Page

def duplicate_is_to_en(page_ids=None) -> tuple[int, int]:
    """
    Copy Icelandic pages (except root) to the English locale.

    If `page_ids` is given, copy only those pages.
    """
    src_locale = Locale.objects.get(language_code="is")
    dst_locale, _ = Locale.objects.get_or_create(language_code="en")

    pages_qs = Page.objects.filter(locale=src_locale).exclude(depth=1)
    if page_ids is not None:
        pages_qs = pages_qs.filter(id__in=page_ids)

    pages = pages_qs.specific().order_by("path")

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
            if page.live:
                new_page.save_revision().publish()
            created += 1

    return created, skipped
