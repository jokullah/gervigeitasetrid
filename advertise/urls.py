from django.urls import path
from .views import AdvertiseView, AdvertiseThanksView, assign_to_project, unregister_from_project, apply_to_project

app_name = 'advertise'

urlpatterns = [
    path("advertise/", AdvertiseView.as_view(), name="advertise-project"),
    path("advertise/thanks/", AdvertiseThanksView.as_view(), name="advertise-thanks"),
    path('assign-to-project/<int:page_id>/', assign_to_project, name='assign_to_project'),
    path('unregister-from-project/<int:page_id>/', unregister_from_project, name='unregister_from_project'),
    path('apply/<int:page_id>/', apply_to_project, name='apply_to_project'),
]