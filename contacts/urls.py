from django.urls import path

from .views import ContactSyncView

urlpatterns = [path("sync/", ContactSyncView.as_view(), name="contacts-sync")]
