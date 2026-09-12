from rest_framework import serializers

from .models import MediaAsset


class PresignSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=MediaAsset.Type.choices)
    content_type = serializers.CharField(max_length=100)
    size = serializers.IntegerField(min_value=1)
    conversation_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = (
            "id",
            "conversation_id",
            "type",
            "statut",
            "content_type",
            "taille_octets",
            "duree",
            "date_creation",
        )
        read_only_fields = fields
