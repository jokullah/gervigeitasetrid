from django.urls import path
from .views import bulk_copy_is_to_en      # the view you already wrote

# tell Django what this mini-module is called ⬇︎
app_name = "bulk_copy"            #  ← add this line

urlpatterns = [
    path("",                      # /admin/bulk-copy/   (root of namespace)
         bulk_copy_is_to_en,
         name="bulk_copy_is_en"),
]
