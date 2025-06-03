from django.urls import path
from .views import AdvertiseView, AdvertiseThanksView

urlpatterns = [
    path("advertise/", AdvertiseView.as_view(), name="advertise-project"),
    path("advertise/thanks/", AdvertiseThanksView.as_view(), name="advertise-thanks"),
]
