from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .pagination import MessageCursorPagination
from .selectors import messages_for_user, search_messages_for_user
from .serializers import (
    MessageCreateSerializer,
    MessageDeleteSerializer,
    MessageEditSerializer,
    MessageForwardSerializer,
    MessageReactionWriteSerializer,
    MessageSearchSerializer,
    MessageSerializer,
)
from .services import delete_message, edit_message, forward_message, send_message, set_message_reaction


class ConversationMessageView(APIView):
    pagination_class = MessageCursorPagination
    throttle_scope = "messages"

    def get(self, request, conversation_id):
        queryset = messages_for_user(user=request.user, conversation_id=conversation_id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(MessageSerializer(page, many=True).data)

    def post(self, request, conversation_id):
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message, created = send_message(
            sender=request.user,
            conversation_id=conversation_id,
            message_type=serializer.validated_data.pop("type"),
            **serializer.validated_data,
        )
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationMessageSearchView(APIView):
    throttle_scope = "messages"

    def get(self, request, conversation_id):
        serializer = MessageSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        messages = search_messages_for_user(
            user=request.user,
            conversation_id=conversation_id,
            query=serializer.validated_data["q"],
        )
        return Response(MessageSerializer(messages, many=True).data)


class MessageDetailView(APIView):
    throttle_scope = "messages"

    def patch(self, request, message_id):
        serializer = MessageEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = edit_message(
            user=request.user,
            message_id=message_id,
            contenu=serializer.validated_data["contenu"],
        )
        return Response(MessageSerializer(message).data)

    def delete(self, request, message_id):
        serializer = MessageDeleteSerializer(
            data={"mode": request.query_params.get("mode") or request.data.get("mode")}
        )
        serializer.is_valid(raise_exception=True)
        message = delete_message(
            user=request.user,
            message_id=message_id,
            mode=serializer.validated_data["mode"],
        )
        if serializer.validated_data["mode"] == "me":
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(MessageSerializer(message).data)


class MessageForwardView(APIView):
    throttle_scope = "messages"

    def post(self, request, message_id):
        serializer = MessageForwardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        messages = forward_message(
            user=request.user,
            message_id=message_id,
            conversation_ids=serializer.validated_data["conversation_ids"],
        )
        return Response(MessageSerializer(messages, many=True).data, status=status.HTTP_201_CREATED)


class MessageReactionView(APIView):
    throttle_scope = "messages"

    def post(self, request, message_id):
        serializer = MessageReactionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = set_message_reaction(
            user=request.user,
            message_id=message_id,
            emoji=serializer.validated_data["emoji"],
        )
        return Response(MessageSerializer(message).data)

    def delete(self, request, message_id):
        message = set_message_reaction(user=request.user, message_id=message_id)
        return Response(MessageSerializer(message).data)
