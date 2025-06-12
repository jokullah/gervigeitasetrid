from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from django.db.models import Q, Count
from django.utils.translation import get_language
import difflib

from wagtail.models import Page, Locale
# For search query logging (optional)
try:
    from wagtail.contrib.search_promotions.models import Query
except ImportError:
    Query = None
from base.models import Tag  # Adjust import path as needed


def calculate_similarity(a, b):
    """Calculate similarity ratio between two strings (0-1)"""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_fuzzy_matches(search_term, all_terms, similarity_threshold=0.7):
    """Find fuzzy matches for a search term"""
    matches = []
    for term in all_terms:
        similarity = calculate_similarity(search_term, term)
        if similarity >= similarity_threshold:
            matches.append((term, similarity))
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def is_phrase_search(query):
    """Determine if this looks like a phrase search (3+ words or quoted)"""
    return len(query.split()) >= 3 or (query.startswith('"') and query.endswith('"'))


def get_phrase_matches(query, base_queryset):
    """Search for exact phrase or words in close proximity, but more flexible"""
    phrase_results = []
    
    # Remove quotes if present
    clean_query = query.strip('"')
    words = clean_query.split()
    
    # Strategy 1: Exact phrase search (highest priority)
    exact_phrase_results = list(base_queryset.filter(
        Q(title__icontains=clean_query) |
        Q(search_description__icontains=clean_query)
    ).distinct())
    
    # Strategy 2: Flexible word matching
    # Look for pages that contain most of the words, even if not adjacent
    if len(words) >= 2:
        # For each word, find pages that contain it
        word_queries = []
        for word in words:
            word_queries.append(
                Q(title__icontains=word) |
                Q(search_description__icontains=word) |
                Q(slug__icontains=word)
            )
        
        # Find pages that contain at least 2 words from the phrase
        combined_q = Q()
        for i, q in enumerate(word_queries):
            # Each word gets added to the query
            combined_q |= q
        
        # Get all pages that match any of the words
        candidate_pages = list(base_queryset.filter(combined_q).distinct())
        
        # Score pages based on how many words they contain
        scored_pages = []
        for page in candidate_pages:
            score = 0
            page_text = f"{page.title} {page.search_description or ''}".lower()
            
            for word in words:
                if word.lower() in page_text:
                    score += 1
            
            # Only include pages that have at least 2 words or half the words
            min_score = max(2, len(words) // 2)
            if score >= min_score:
                scored_pages.append((page, score))
        
        # Sort by score (descending)
        scored_pages.sort(key=lambda x: x[1], reverse=True)
        flexible_results = [page for page, score in scored_pages]
    else:
        flexible_results = []
    
    # Combine results: exact phrase first, then flexible matches
    seen_ids = set()
    for page in exact_phrase_results:
        if page.id not in seen_ids:
            phrase_results.append(page)
            seen_ids.add(page.id)
    
    for page in flexible_results:
        if page.id not in seen_ids:
            phrase_results.append(page)
            seen_ids.add(page.id)
    
    return phrase_results


def search(request):
    """
    Enhanced language-aware search view with tag support and intelligent matching.
    """
    search_query = request.GET.get("query", "").strip()
    page_number = request.GET.get("page", 1)
    selected_tags = request.GET.getlist("tags")  # For tag filtering
    
    # ------------------------------------------------------------------
    # 1. Work out the active Wagtail locale object
    # ------------------------------------------------------------------
    lang = request.LANGUAGE_CODE[:2]  # 'en-gb' → 'en'
    try:
        active_locale = Locale.objects.get(language_code=lang)
    except Locale.DoesNotExist:
        active_locale = Locale.get_default()

    # ------------------------------------------------------------------
    # 2. Enhanced search logic with fuzzy matching
    # ------------------------------------------------------------------
    search_results = Page.objects.none()
    suggested_tags = []
    did_you_mean_suggestions = []
    search_expanded = False
    expanded_terms = []
    
    if search_query or selected_tags:
        # Start with base queryset
        base_queryset = Page.objects.live().filter(locale=active_locale)
        
        # Check if this is a phrase search
        is_phrase = is_phrase_search(search_query) if search_query else False
        
        # For phrase searches, prioritize phrase matching but still fall back
        if is_phrase and search_query:
            phrase_results = get_phrase_matches(search_query, base_queryset)
            
            # If phrase search found results, use those plus regular search as backup
            if phrase_results:
                # Also do regular search for broader results
                exact_search = base_queryset.search(search_query)
                exact_results = list(exact_search)
                
                # Combine phrase results (higher priority) with regular search
                all_found_pages = []
                seen_ids = set()
                
                # Add phrase matches first
                for page in phrase_results:
                    if page.id not in seen_ids:
                        all_found_pages.append(page)
                        seen_ids.add(page.id)
                
                # Add regular search results as backup
                for page in exact_results:
                    if page.id not in seen_ids:
                        all_found_pages.append(page)
                        seen_ids.add(page.id)
                
                # Apply tag filtering if selected
                if selected_tags:
                    found_page_ids = [page.id for page in all_found_pages]
                    search_results = base_queryset.filter(
                        id__in=found_page_ids,
                        tagged_items__tag__id__in=selected_tags
                    ).distinct()
                else:
                    found_page_ids = [page.id for page in all_found_pages]
                    search_results = base_queryset.filter(id__in=found_page_ids)
                
                # Get suggested tags for phrase searches
                suggested_tags = Tag.objects.filter(
                    Q(name_en__icontains=search_query) | 
                    Q(name_is__icontains=search_query)
                )[:10]
                
            else:
                # No phrase results found, fall back to regular search
                is_phrase = False  # Switch to regular search mode
        
        if not is_phrase:
            # Regular search logic (not a phrase, or phrase search fell back)
            # Initialize variables
            fuzzy_expanded_terms = []
            
            # Get all searchable content for fuzzy matching
            if search_query:
                # Get all page titles and tag names for fuzzy matching
                all_page_titles = list(base_queryset.values_list('title', flat=True))
                all_tag_names = []
                current_lang = get_language()
                
                for tag in Tag.objects.all():
                    if current_lang and current_lang.startswith('is'):
                        all_tag_names.extend([tag.name_is, tag.name_en])
                    else:
                        all_tag_names.extend([tag.name_en, tag.name_is])
                
                # Remove empty strings and duplicates
                all_searchable_terms = list(set([term for term in all_page_titles + all_tag_names if term]))
                
                # Extract individual words from search query for fuzzy matching
                search_words = search_query.split()
                fuzzy_expanded_terms = []
                
                for word in search_words:
                    if len(word) >= 3:  # Only do fuzzy matching for words 3+ characters
                        # Find fuzzy matches for each word
                        word_matches = get_fuzzy_matches(word, all_searchable_terms, similarity_threshold=0.75)
                        
                        if word_matches:
                            # If we have very close matches (90%+), automatically expand search
                            very_close_matches = [match[0] for match in word_matches if match[1] >= 0.9]
                            
                            # Only include matches that are actually different from the original word
                            different_matches = [match for match in very_close_matches if match.lower() != word.lower()]
                            
                            if different_matches:
                                fuzzy_expanded_terms.extend(different_matches[:3])  # Limit to top 3
                                search_expanded = True
                                expanded_terms.extend(different_matches[:3])
                            
                            # For "did you mean" suggestions (75-89% similarity)
                            suggestion_matches = [match[0] for match in word_matches if 0.75 <= match[1] < 0.9]
                            # Only suggest terms that are different from the original
                            different_suggestions = [match for match in suggestion_matches if match.lower() != word.lower()]
                            if different_suggestions and not different_matches:
                                did_you_mean_suggestions.extend(different_suggestions[:3])
            
            # Strategy 1: Exact Wagtail search (highest priority)
            exact_results = []
            if search_query:
                exact_search = base_queryset.search(search_query)
                exact_results = list(exact_search)
            
            # Strategy 2: Fuzzy expanded search (if we found close matches)
            fuzzy_results = []
            if fuzzy_expanded_terms:
                for fuzzy_term in fuzzy_expanded_terms:
                    fuzzy_search = base_queryset.search(fuzzy_term)
                    fuzzy_results.extend(list(fuzzy_search))
            
            # Strategy 3: Tag-based search (including fuzzy tag matches)
            tag_results = []
            matching_tags = []
            
            if search_query:
                # Find tags that match the search query (exact and fuzzy)
                search_terms_for_tags = [search_query] + fuzzy_expanded_terms
                
                for search_term in search_terms_for_tags:
                    current_lang = get_language()
                    if current_lang and current_lang.startswith('is'):
                        term_matching_tags = Tag.objects.filter(
                            Q(name_is__icontains=search_term) | 
                            Q(name_en__icontains=search_term)
                        )
                    else:
                        term_matching_tags = Tag.objects.filter(
                            Q(name_en__icontains=search_term) | 
                            Q(name_is__icontains=search_term)
                        )
                    matching_tags.extend(list(term_matching_tags))
                
                # Remove duplicates
                matching_tags = list(set(matching_tags))
                
                # Get pages tagged with matching tags
                if matching_tags:
                    tag_results = list(base_queryset.filter(
                        tagged_items__tag__in=matching_tags
                    ).distinct())
            
            # Strategy 4: Partial text search (cast a wide net, including fuzzy terms)
            partial_results = []
            if search_query:
                search_terms_for_partial = [search_query] + fuzzy_expanded_terms
                q_objects = Q()
                
                for search_term in search_terms_for_partial:
                    for word in search_term.split():
                        q_objects |= (
                            Q(title__icontains=word) |
                            Q(search_description__icontains=word) |
                            Q(slug__icontains=word)
                        )
                
                partial_results = list(base_queryset.filter(q_objects).distinct())
            
            # Combine all search results (cast wide net, then filter by tags if needed)
            all_found_pages = []
            seen_ids = set()
            
            # Add exact matches first (highest priority)
            for page in exact_results:
                if page.id not in seen_ids:
                    all_found_pages.append(page)
                    seen_ids.add(page.id)
            
            # Add fuzzy matches
            for page in fuzzy_results:
                if page.id not in seen_ids:
                    all_found_pages.append(page)
                    seen_ids.add(page.id)
            
            # Add tag matches
            for page in tag_results:
                if page.id not in seen_ids:
                    all_found_pages.append(page)
                    seen_ids.add(page.id)
            
            # Add partial matches (cast wide net)
            for page in partial_results:
                if page.id not in seen_ids:
                    all_found_pages.append(page)
                    seen_ids.add(page.id)
            
            # Now apply tag filtering if tags are selected
            if search_query and selected_tags:
                # Filter the combined results by selected tags
                found_page_ids = [page.id for page in all_found_pages]
                search_results = base_queryset.filter(
                    id__in=found_page_ids,
                    tagged_items__tag__id__in=selected_tags
                ).distinct()
            elif search_query:
                # Use all found pages
                found_page_ids = [page.id for page in all_found_pages]
                if found_page_ids:
                    search_results = base_queryset.filter(id__in=found_page_ids)
                else:
                    search_results = Page.objects.none()
            elif selected_tags:
                # Only tag filtering - show pages with selected tags
                search_results = base_queryset.filter(
                    tagged_items__tag__id__in=selected_tags
                ).distinct()
            else:
                search_results = Page.objects.none()
            
            # Get suggested tags for the search interface (including fuzzy matches)
            if search_query:
                search_terms_for_suggestions = [search_query] + fuzzy_expanded_terms
                suggested_tags_set = set()
                
                for search_term in search_terms_for_suggestions:
                    term_suggestions = Tag.objects.filter(
                        Q(name_en__icontains=search_term) | 
                        Q(name_is__icontains=search_term)
                    )
                    suggested_tags_set.update(term_suggestions)
                
                suggested_tags = list(suggested_tags_set)[:10]
        
        # Log the query for analytics (if Query model is available)
        if search_query and Query:
            query = Query.get(search_query)
            query.add_hit()
    
    # ------------------------------------------------------------------
    # 3. Get all available tags for filtering interface
    # ------------------------------------------------------------------
    all_tags = Tag.objects.all().order_by('name_en')
    
    # ------------------------------------------------------------------
    # 4. Convert to specific page instances and paginate
    # ------------------------------------------------------------------
    # Convert search results to specific page instances
    if search_results:
        # Get the specific page instances instead of generic Page instances
        specific_pages = []
        for page in search_results:
            # Get the specific page instance
            specific_page = page.specific
            specific_pages.append(specific_page)
        
        # Re-create the paginated results with specific instances
        paginator = Paginator(specific_pages, 10)
        try:
            search_results = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            search_results = paginator.page(1)
    else:
        # Paginate empty results
        paginator = Paginator([], 10)
        try:
            search_results = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            search_results = paginator.page(1)

    # ------------------------------------------------------------------
    # 5. Render
    # ------------------------------------------------------------------
    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
            "suggested_tags": suggested_tags,
            "all_tags": all_tags,
            "selected_tags": [int(tag_id) for tag_id in selected_tags if tag_id.isdigit()],
            "did_you_mean_suggestions": did_you_mean_suggestions,
            "search_expanded": search_expanded,
            "expanded_terms": expanded_terms,
            "is_phrase_search": is_phrase if search_query else False,
        },
    )


def tag_search(request, tag_id):
    """
    Dedicated view for searching by a specific tag.
    """
    try:
        tag = Tag.objects.get(id=tag_id)
    except Tag.DoesNotExist:
        from django.shortcuts import redirect
        return redirect('search')
    
    # Get current locale
    lang = request.LANGUAGE_CODE[:2]
    try:
        active_locale = Locale.objects.get(language_code=lang)
    except Locale.DoesNotExist:
        active_locale = Locale.get_default()
    
    # Get all pages with this tag
    tagged_pages = Page.objects.live().filter(
        locale=active_locale,
        tagged_items__tag=tag
    ).distinct()
    
    # Paginate
    paginator = Paginator(tagged_pages, 10)
    page_number = request.GET.get("page", 1)
    
    try:
        search_results = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        search_results = paginator.page(1)
    
    return TemplateResponse(
        request,
        "search/tag_search.html",
        {
            "tag": tag,
            "search_results": search_results,
            "search_query": f"#{tag.name}",
        },
    )
