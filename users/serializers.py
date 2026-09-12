from rest_framework import serializers

from media.storage import presigned_read_url

from .models import User


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, user):
        return presigned_read_url(user.avatar_url)

    class Meta:
        model = User
        fields = ("id", "telephone", "email", "nom_affichage", "avatar_url", "statut", "statut_personnalise", "date_creation")
        read_only_fields = fields


class PublicUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, user):
        return presigned_read_url(user.avatar_url)

    class Meta:
        model = User
        fields = ("id", "nom_affichage", "avatar_url", "statut", "statut_personnalise")
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    telephone = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False, allow_blank=False)
    password = serializers.CharField(write_only=True, min_length=10, trim_whitespace=False)
    nom_affichage = serializers.CharField(max_length=150)

    def validate(self, attrs):
        if not attrs.get("telephone") and not attrs.get("email"):
            raise serializers.ValidationError("Un téléphone ou un email est obligatoire.")
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    code = serializers.RegexField(r"^\d{6}$")


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ResendOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class ProfileUpdateSerializer(serializers.Serializer):
    nom_affichage = serializers.CharField(max_length=150, required=False)
    statut_personnalise = serializers.CharField(max_length=80, required=False, allow_blank=True)
    avatar_media_id = serializers.IntegerField(min_value=1, required=False)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=10, trim_whitespace=False)
