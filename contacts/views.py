from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import PublicUserSerializer

from .serializers import ContactSyncSerializer
from .services import synchronize_contacts


class ContactSyncView(APIView):
    throttle_scope = "contacts"

    def post(self, request):
        serializer = ContactSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            users = synchronize_contacts(
                owner=request.user,
                phone_numbers=serializer.validated_data["telephones"],
            )
        except (DjangoValidationError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"registered_contacts": PublicUserSerializer(users, many=True).data})
