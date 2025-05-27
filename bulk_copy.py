"""
bulk_copy.py  –  duplicate the Icelandic tree into English
⇢ compatible with Wagtail 6 & 7 (uses only parameters that exist in both)
"""

# notkun: inn í top foldernum með env kveikt á, keyra python manage.py shell < bulk_copy.py  

from django.db import transaction
from wagtail.models import Locale, Page

# ──────────────────────────────────────────────────────────────────────────────
# 1 ▪ get the source + destination Locale rows
# ──────────────────────────────────────────────────────────────────────────────
src_locale = Locale.objects.get(language_code="is")        #  → Icelandic
dst_locale, _ = Locale.objects.get_or_create(language_code="en")  #  → English

# ──────────────────────────────────────────────────────────────────────────────
# 2 ▪ walk the Icelandic pages top-down (parents before children)
# ──────────────────────────────────────────────────────────────────────────────
pages = (
    Page.objects
    .filter(locale=src_locale)
    .exclude(depth=1)           # skip the single site-root page itself
    .specific()                 # return real subclasses
    .order_by("path")           # top-down order
)

created = 0
skipped = 0

with transaction.atomic():      # single DB transaction, easy to roll back
    for page in pages:

        # already has an English sibling? → skip
        if Page.objects.filter(
            translation_key=page.translation_key,
            locale=dst_locale
        ).exists():
            skipped += 1
            continue

        # ── copy the page ───────────────────────────────────────────────────
        new_page = page.copy_for_translation(
            locale=dst_locale,
            copy_parents=True,   # auto-copy missing ancestors first
            alias=False,         # real copy (so you can edit independently)
        )

        # keep the live/draft status in sync
        if page.live:
            # publish=True is gone in Wagtail 7 – publish manually
            new_page.save_revision().publish()
        created += 1

print(f"✓  {created} pages copied; {skipped} already had an English version.")
