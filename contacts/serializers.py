from rest_framework import serializers

from users.serializers import PublicUserSerializer


class ContactSyncSerializer(serializers.Serializer):
    telephones = serializers.ListField(
        child=serializers.CharField(max_length=32),
        allow_empty=True,
        max_length=1000,
    )


class ContactSyncResultSerializer(serializers.Serializer):
    registered_contacts = PublicUserSerializer(many=True)
