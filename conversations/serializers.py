from rest_framework import serializers

from media.storage import presigned_read_url
from users.serializers import PublicUserSerializer

from .models import Conversation, Membership


class MembershipSerializer(serializers.ModelSerializer):
    utilisateur = PublicUserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "utilisateur", "role", "date_ajout")


class ConversationSerializer(serializers.ModelSerializer):
    membres = MembershipSerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, conversation):
        return presigned_read_url(conversation.avatar_url)

    class Meta:
        model = Conversation
        fields = ("id", "type", "nom", "avatar_url", "envoi_messages", "date_creation", "membres")


class ConversationCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Conversation.Type.choices)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=255,
    )
    nom = serializers.CharField(max_length=150, required=False, allow_blank=False)
    avatar_media_id = serializers.IntegerField(min_value=1, required=False)


class GroupUpdateSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=150, required=False, allow_blank=False)
    avatar_media_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    envoi_messages = serializers.ChoiceField(
        choices=Conversation.EnvoiMessages.choices,
        required=False,
    )


class MembershipRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Membership.Role.choices)


class GlobalSearchSerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=150)
