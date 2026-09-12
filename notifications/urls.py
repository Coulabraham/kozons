from django.urls import path

from .views import PushSubscriptionView

urlpatterns = [
    path("subscriptions/", PushSubscriptionView.as_view(), name="push-subscription")
]
