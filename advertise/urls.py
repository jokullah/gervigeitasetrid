from django.urls import path
from .views import AdvertiseView, AdvertiseThanksView, assign_to_project

app_name = 'advertise'

urlpatterns = [
    path("advertise/", AdvertiseView.as_view(), name="advertise-project"),
    path("advertise/thanks/", AdvertiseThanksView.as_view(), name="advertise-thanks"),
    path('assign-to-project/<int:page_id>/', assign_to_project, name='assign_to_project'),
]
