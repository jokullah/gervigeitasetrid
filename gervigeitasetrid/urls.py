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
from .auth_views import login, signup

# Simple view for the auth page
def auth_page(request):
    return render(request, 'auth.html')

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("admin/hide-translation-notice/", hide_translation_notice),
    path("", include("advertise.urls")),
]

urlpatterns += i18n_patterns(
    path('search/', search_views.search, name='search'),
    path("i18n/", include("django.conf.urls.i18n")),
    path("login/", login, name="login"),
    path("signup/", signup, name="signup"),
    path("auth/", auth_page, name="auth"),
    path("", include("wagtail.urls")),
)


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
