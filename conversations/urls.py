from django.urls import path

from .views import (
    ConversationDetailView,
    ConversationLeaveView,
    ConversationListCreateView,
    GlobalSearchView,
    GroupMemberDetailView,
    GroupMemberRoleView,
)

urlpatterns = [
    path("", ConversationListCreateView.as_view(), name="conversation-list-create"),
    path("search/", GlobalSearchView.as_view(), name="conversation-search"),
    path("<int:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("<int:conversation_id>/leave/", ConversationLeaveView.as_view(), name="conversation-leave"),
    path(
        "<int:conversation_id>/members/<int:user_id>/",
        GroupMemberDetailView.as_view(),
        name="group-member-detail",
    ),
    path(
        "<int:conversation_id>/members/<int:user_id>/role/",
        GroupMemberRoleView.as_view(),
        name="group-member-role",
    ),
]
