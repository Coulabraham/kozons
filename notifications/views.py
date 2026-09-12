from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PushSubscriptionSerializer
from .services import register_push_subscription


class PushSubscriptionView(APIView):
    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = register_push_subscription(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(
            PushSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )
