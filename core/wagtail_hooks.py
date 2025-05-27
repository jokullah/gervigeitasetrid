# core/wagtail_hooks.py
from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from core import wagtail_bulk_copy_urls as bc_urls


@hooks.register("register_admin_urls")
def register_bulk_copy_urls():
    return [path("bulk-copy/", include(bc_urls, namespace="bulk_copy"))]


@hooks.register("register_settings_menu_item")
def register_bulk_copy_menu_item():
    # NOTE: no “permissions=” kwarg – the view itself is permission-gated
    return MenuItem(
        _("Clone IS → EN pages"),
        reverse("bulk_copy:bulk_copy_is_en"),
        icon_name="copy",
        order=1000,                # put it at the bottom of the Settings list
    )
