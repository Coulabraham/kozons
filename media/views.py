from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MediaAssetSerializer, PresignSerializer
from .services import complete_upload, create_presigned_upload, serialize_asset


class PresignUploadView(APIView):
    throttle_scope = "uploads"

    def post(self, request):
        serializer = PresignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset, upload = create_presigned_upload(
            user=request.user,
            media_type=serializer.validated_data.pop("type"),
            **serializer.validated_data,
        )
        return Response(
            {"asset": MediaAssetSerializer(asset).data, "upload": upload},
            status=status.HTTP_201_CREATED,
        )


class CompleteUploadView(APIView):
    throttle_scope = "uploads"

    def post(self, request, asset_id):
        asset, accepted = complete_upload(user=request.user, asset_id=asset_id)
        return Response(
            serialize_asset(asset),
            status=status.HTTP_202_ACCEPTED if accepted else status.HTTP_200_OK,
        )


class MediaAssetDetailView(APIView):
    throttle_scope = "uploads"

    def get(self, request, asset_id):
        from rest_framework.exceptions import NotFound

        from .models import MediaAsset

        try:
            asset = MediaAsset.objects.get(pk=asset_id, utilisateur=request.user)
        except MediaAsset.DoesNotExist as exc:
            raise NotFound("Média introuvable.") from exc
        return Response(serialize_asset(asset))
