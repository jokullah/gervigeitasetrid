# core/wagtail_bulk_copy_views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from wagtail.models import Page, Locale


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
    if request.method == "POST":
        page_ids = request.POST.getlist("pages")
        dst_lang = request.POST["dst_lang"]
        dst_locale = Locale.objects.get(language_code=dst_lang)

        created = 0
        skipped = 0
        for page_id in page_ids:
            page = Page.objects.get(id=page_id).specific
            if Page.objects.filter(translation_key=page.translation_key, locale=dst_locale).exists():
                skipped += 1
                continue
            new_page = page.copy_for_translation(locale=dst_locale, copy_parents=True, alias=False)
            if page.live:
                new_page.save_revision().publish()
            created += 1

        messages.success(request, f"✅ {created} copied, {skipped} skipped.")
        return redirect(reverse("wagtailadmin_home"))

    return render(request, "bulk_copy/chooser.html", {
        "is_to_en": get_untranslated_pages("is", "en"),
        "en_to_is": get_untranslated_pages("en", "is"),
    })
