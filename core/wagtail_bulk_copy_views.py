# core/wagtail_bulk_copy_views.py
from django.contrib.admin.utils import quote
from django.contrib.auth.decorators import permission_required, login_required
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages

from core.bulk_copy import duplicate_is_to_en

@login_required
@permission_required("wagtailadmin.access_admin", raise_exception=True)
def bulk_copy_view(request):
    if request.method == "POST":
        created, skipped = duplicate_is_to_en()
        messages.success(
            request,
            f"✅ {created} pages copied. {skipped} already had an English version.",
        )
        # Kick the user back to wherever they came from
        return redirect(reverse("wagtailadmin_home"))

    # GET → confirmation screen
    return render(request, "bulk_copy/confirm.html")
