from django.http import JsonResponse
from django.urls import include, path
from users.views import ProfileView


def health(_request):
    return JsonResponse({"status": "ok", "service": "kozons-api"})


urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/auth/", include("users.urls")),
    path("api/profile/", ProfileView.as_view(), name="profile"),
    path("api/contacts/", include("contacts.urls")),
    path("api/conversations/", include("conversations.urls")),
    path("api/", include("messaging.urls")),
    path("api/media/", include("media.urls")),
    path("api/notifications/", include("notifications.urls")),
]
