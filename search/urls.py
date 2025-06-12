# search/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.search, name='search'),
    path('tag/<int:tag_id>/', views.tag_search, name='tag_search'),
    path('live/', views.live_search, name='live_search'),
]
