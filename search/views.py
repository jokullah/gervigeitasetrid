from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse

from wagtail.models import Page, Locale
# If you use “Promoted search results”, leave this import uncommented
# from wagtail.contrib.search_promotions.models import Query


def search(request):
    """
    Language-aware search view.
    Only pages whose locale matches request.LANGUAGE_CODE are shown.
    """
    search_query = request.GET.get("query", "").strip()
    page_number  = request.GET.get("page", 1)

    # ------------------------------------------------------------------
    # 1.  Work out the active Wagtail locale object
    # ------------------------------------------------------------------
    lang = request.LANGUAGE_CODE[:2]  # 'en-gb' → 'en';
    try:
        active_locale = Locale.objects.get(language_code=lang)
    except Locale.DoesNotExist:
        active_locale = Locale.get_default()

    # ------------------------------------------------------------------
    # 2.  Do the search, restricted to that locale
    # ------------------------------------------------------------------
    if search_query:
        search_results = (
            Page.objects.live()
                .filter(locale=active_locale)        # ← key line
                .search(search_query)
        )

        # If you use promoted search results, log the query
        # query = Query.get(search_query)
        # query.add_hit()
    else:
        search_results = Page.objects.none()

    # ------------------------------------------------------------------
    # 3.  Paginate
    # ------------------------------------------------------------------
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        search_results = paginator.page(1)

    # ------------------------------------------------------------------
    # 4.  Render
    # ------------------------------------------------------------------
    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
        },
    )
