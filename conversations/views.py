from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import PublicUserSerializer

from .selectors import conversations_for_user, search_conversations_and_contacts
from .serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    GlobalSearchSerializer,
    GroupUpdateSerializer,
    MembershipRoleSerializer,
)
from .services import (
    create_conversation,
    leave_conversation,
    remove_group_member,
    set_group_member_role,
    update_group,
)


class ConversationListCreateView(APIView):
    def get(self, request):
        conversations = conversations_for_user(request.user)
        return Response(ConversationSerializer(conversations, many=True).data)

    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation, created = create_conversation(
            creator=request.user,
            **serializer.validated_data,
        )
        conversation = conversations_for_user(request.user).get(pk=conversation.pk)
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationLeaveView(APIView):
    def delete(self, request, conversation_id):
        leave_conversation(user=request.user, conversation_id=conversation_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationDetailView(APIView):
    def patch(self, request, conversation_id):
        serializer = GroupUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = update_group(
            user=request.user,
            conversation_id=conversation_id,
            **serializer.validated_data,
        )
        conversation = conversations_for_user(request.user).get(pk=conversation.pk)
        return Response(ConversationSerializer(conversation).data)


class GroupMemberDetailView(APIView):
    def delete(self, request, conversation_id, user_id):
        remove_group_member(
            user=request.user,
            conversation_id=conversation_id,
            member_user_id=user_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupMemberRoleView(APIView):
    def patch(self, request, conversation_id, user_id):
        serializer = MembershipRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = set_group_member_role(
            user=request.user,
            conversation_id=conversation_id,
            member_user_id=user_id,
            role=serializer.validated_data["role"],
        )
        return Response({"user_id": membership.utilisateur_id, "role": membership.role})


class GlobalSearchView(APIView):
    def get(self, request):
        serializer = GlobalSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        conversations, contacts = search_conversations_and_contacts(
            user=request.user,
            query=serializer.validated_data["q"],
        )
        return Response(
            {
                "conversations": ConversationSerializer(conversations, many=True).data,
                "contacts": PublicUserSerializer(contacts, many=True).data,
            }
        )
