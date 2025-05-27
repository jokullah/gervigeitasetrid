# core/bulk_copy.py
from django.db import transaction
from wagtail.models import Locale, Page

def duplicate_is_to_en() -> tuple[int, int]:
    """
    Copy every Icelandic page (except the site root) into the English locale.

    Returns
    -------
    (created, skipped)  # numbers of pages
    """
    src_locale = Locale.objects.get(language_code="is")
    dst_locale, _ = Locale.objects.get_or_create(language_code="en")

    pages = (
        Page.objects
        .filter(locale=src_locale)
        .exclude(depth=1)      # skip site root
        .specific()
        .order_by("path")      # parents before children
    )

    created = skipped = 0
    with transaction.atomic():
        for page in pages:
            # Skip if a translation already exists
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
