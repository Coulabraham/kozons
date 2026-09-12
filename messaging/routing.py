from django.urls import re_path

from .consumers import ConversationConsumer, UserConsumer

websocket_urlpatterns = [
    re_path(r"^ws/users/me/$", UserConsumer.as_asgi()),
    re_path(
        r"^ws/conversations/(?P<conversation_id>\d+)/$",
        ConversationConsumer.as_asgi(),
    )
]
