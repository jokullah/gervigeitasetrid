def starfsmenn_person_pages(request):
    """
    Add starfsmenn person pages to all template contexts
    """
    try:
        from people.models import PersonPage
        from django.utils import translation
        
        # Get all live PersonPage objects for use in templates
        person_pages = PersonPage.objects.live()
        
        # Check if current user has a PersonPage (for Starfsmenn users)
        user_person_page = None
        if request.user.is_authenticated:
            # Check if user is in Starfsmenn group
            is_starfsmenn = request.user.groups.filter(name='Starfsmenn').exists()
            if is_starfsmenn:
                # Try to find their PersonPage, preferring current language
                current_language = translation.get_language()
                user_pages = person_pages.filter(email=request.user.email)
                
                if user_pages.exists():
                    # Try to get the page in current language first
                    current_lang_page = user_pages.filter(locale__language_code=current_language[:2]).first()
                    if current_lang_page:
                        user_person_page = current_lang_page
                    else:
                        # Fallback to any available page
                        user_person_page = user_pages.first()
        
        return {
            'starfsmenn_person_pages': person_pages,
            'user_person_page': user_person_page,
            'user_is_starfsmenn': request.user.is_authenticated and request.user.groups.filter(name='Starfsmenn').exists()
        }
    except ImportError:
        # If people app doesn't exist, return empty values
        return {
            'starfsmenn_person_pages': [],
            'user_person_page': None,
            'user_is_starfsmenn': False
        }