# core/wagtail_hooks.py
from django.urls import include, path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.ui.components import Component
from django.templatetags.static import static
from django.utils.translation import gettext_lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.models import Locale, Page
from core import wagtail_bulk_copy_urls as bc_urls


@hooks.register("register_admin_urls")
def register_bulk_copy_urls():
    return [path("bulk-copy/", include(bc_urls, namespace="bulk_copy"))]


@hooks.register("register_settings_menu_item")
def register_bulk_copy_menu_item():
    return MenuItem(
        gettext_lazy("Clone IS ↔ EN pages"),
        reverse("bulk_copy:bulk_copy_is_en"),
        icon_name="copy",
        order=1000,
    )


@hooks.register("insert_global_admin_css")
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static("css/admin_notice.css"))


@hooks.register("insert_global_admin_js")
def global_admin_js():
    return format_html('<script src="{}"></script>', static("js/admin_notice.js"))


class TranslationAlertBanner(Component):
    name = "translation-alert-banner"
    order = 0  # ✅ Fixes the error

    def render_html(self, parent_context):
        request = parent_context["request"]
        if request.session.get("hide_translation_notice"):
            return ""

        try:
            is_locale = Locale.objects.get(language_code="is")
            en_locale = Locale.objects.get(language_code="en")

            is_to_en = Page.objects.filter(locale=is_locale).exclude(depth=1).exclude(
                translation_key__in=Page.objects.filter(locale=en_locale).values_list("translation_key", flat=True)
            )

            en_to_is = Page.objects.filter(locale=en_locale).exclude(depth=1).exclude(
                translation_key__in=Page.objects.filter(locale=is_locale).values_list("translation_key", flat=True)
            )

            if not (is_to_en.exists() or en_to_is.exists()):
                return ""

            chooser_url = reverse("bulk_copy:bulk_copy_is_en")
            return mark_safe(f"""
                <div class="translation-alert" style="background: #fff3cd; border: 1px solid #ffeeba; padding: 1em; margin-bottom: 2em;">
                    <strong>⚠️ Some pages exist only in one language.</strong><br>
                    <a href="{chooser_url}" class="button button-small button-primary" style="margin-top: 0.5em;">Review untranslated pages</a>
                    <button onclick="this.parentElement.style.display='none'" class="button button-small" style="margin-left: 1em;">Dismiss</button>
                </div>
            """)
        except Exception:
            return ""


@hooks.register("construct_homepage_panels")
def add_translation_notice(request, panels):
    panels.append(TranslationAlertBanner())
