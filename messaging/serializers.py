from rest_framework import serializers

from media.storage import presigned_read_url

from .models import Message, MessageReaction, MessageReceipt


class MessageReceiptSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="utilisateur_id", read_only=True)

    class Meta:
        model = MessageReceipt
        fields = ("user_id", "statut", "date_maj")


class MessageReactionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="utilisateur_id", read_only=True)

    class Meta:
        model = MessageReaction
        fields = ("user_id", "emoji")


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="utilisateur_expediteur_id", read_only=True)
    receipts = MessageReceiptSerializer(source="statuts", many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    media_url = serializers.SerializerMethodField()
    contenu = serializers.SerializerMethodField()
    duree = serializers.SerializerMethodField()
    transfere = serializers.SerializerMethodField()

    def get_media_url(self, message):
        if message.supprime_pour_tous_le:
            return None
        return presigned_read_url(message.media_url)

    def get_contenu(self, message):
        return None if message.supprime_pour_tous_le else message.contenu

    def get_duree(self, message):
        return None if message.supprime_pour_tous_le else message.duree

    def get_transfere(self, message):
        return message.conversation_origine_id is not None

    class Meta:
        model = Message
        fields = (
            "id",
            "client_id",
            "conversation_id",
            "sender_id",
            "type",
            "contenu",
            "media_url",
            "duree",
            "date_envoi",
            "modifie_le",
            "supprime_pour_tous_le",
            "transfere",
            "receipts",
            "reactions",
        )


class MessageCreateSerializer(serializers.Serializer):
    client_id = serializers.UUIDField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=Message.Type.choices)
    contenu = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=10000)
    media_asset_id = serializers.IntegerField(required=False, allow_null=True, min_value=1, write_only=True)
    duree = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class MessageEditSerializer(serializers.Serializer):
    contenu = serializers.CharField(max_length=10000, allow_blank=False)


class MessageDeleteSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=("me", "everyone"))


class MessageForwardSerializer(serializers.Serializer):
    conversation_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=20,
    )


class MessageReactionWriteSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=16)


class MessageSearchSerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=200)
