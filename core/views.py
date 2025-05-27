# core/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .bulk_copy import duplicate_is_to_en

@login_required
@permission_required("wagtailadmin.access_admin", raise_exception=True)
def bulk_copy_is_to_en(request):
    """
    Admin action: copy every Icelandic page to the English locale.
    """
    if request.method == "POST":
        created, skipped = duplicate_is_to_en()
        messages.success(
            request,
            f"✅ {created} pages copied; {skipped} already existed.",
        )
        return redirect(reverse("wagtailadmin_home"))

    # GET → show confirmation template
    return render(request, "bulk_copy/confirm.html")
