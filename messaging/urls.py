from django.urls import path

from .views import (
    ConversationMessageSearchView,
    ConversationMessageView,
    MessageDetailView,
    MessageForwardView,
    MessageReactionView,
)

urlpatterns = [
    path(
        "conversations/<int:conversation_id>/messages/",
        ConversationMessageView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<int:conversation_id>/messages/search/",
        ConversationMessageSearchView.as_view(),
        name="conversation-message-search",
    ),
    path("messages/<int:message_id>/", MessageDetailView.as_view(), name="message-detail"),
    path("messages/<int:message_id>/forward/", MessageForwardView.as_view(), name="message-forward"),
    path("messages/<int:message_id>/reaction/", MessageReactionView.as_view(), name="message-reaction"),
]
