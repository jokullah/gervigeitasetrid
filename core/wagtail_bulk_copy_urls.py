# core/wagtail_bulk_copy_urls.py

from django.urls import path
from .wagtail_bulk_copy_views import bulk_copy_view  # <-- ✅ this is the updated view

app_name = "bulk_copy"

urlpatterns = [
    path("", bulk_copy_view, name="bulk_copy_is_en"),
]
