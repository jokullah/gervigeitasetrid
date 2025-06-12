from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.shortcuts import render

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

from core.views import hide_translation_notice
from .auth_views import login, signup, logout, forgot_password, verify_email, resend_verification, reset_password
from advertise.views import verify_project_ad  # ADD THIS LINE

# Simple view for the auth page
def auth_page(request):
    return render(request, 'auth.html')

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("admin/hide-translation-notice/", hide_translation_notice),
]

urlpatterns += i18n_patterns(
    path('search/', include('search.urls')),
    path("i18n/", include("django.conf.urls.i18n")),
    path("login/", login, name="login"),
    path("signup/", signup, name="signup"),
    path("logout/", logout, name="logout"),
    path("auth/", auth_page, name="auth"),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-email/<uuid:verification_code>/', verify_email, name='verify_email'),
    path('resend-verification/', resend_verification, name='resend_verification'),
    path('reset-password/<uuid:reset_code>/', reset_password, name='reset_password'),
    path('verify-project-ad/<uuid:verification_code>/', verify_project_ad, name='verify_project_ad'),  # ADD THIS LINE
    path('advertise/', include('advertise.urls')),  # Advertise URLs
    path("", include("wagtail.urls")),  # Keep this last as catch-all
)

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)