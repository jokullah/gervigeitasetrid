from django.shortcuts import render
from .models import EventPage

# Create your views here.

def event_tag_filtered(request):
    tag = request.GET.get('tag')
    events = EventPage.objects.live().filter(tags__name=tag) if tag else EventPage.objects.none()
    
    return render(request, 'event/event_tag_filtered.html', {
        'events': events,
        'current_tag': tag,
    })
