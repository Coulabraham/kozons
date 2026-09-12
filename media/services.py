import hashlib
import hmac
import uuid
from pathlib import PurePosixPath

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from kozons.rate_limit import enforce_rate_limit

from conversations.models import Membership

from .models import MediaAsset
from .storage import object_reference, presigned_read_url, s3_client


MEDIA_RULES = {
    MediaAsset.Type.IMAGE: {
        "image/jpeg": ("jpg", 20 * 1024 * 1024),
        "image/png": ("png", 20 * 1024 * 1024),
        "image/webp": ("webp", 20 * 1024 * 1024),
    },
    MediaAsset.Type.VIDEO: {
        "video/mp4": ("mp4", 250 * 1024 * 1024),
        "video/quicktime": ("mov", 250 * 1024 * 1024),
        "video/webm": ("webm", 250 * 1024 * 1024),
    },
    MediaAsset.Type.NOTE_VOCALE: {
        "audio/ogg": ("ogg", 30 * 1024 * 1024),
        "audio/webm": ("webm", 30 * 1024 * 1024),
        "audio/mpeg": ("mp3", 30 * 1024 * 1024),
        "audio/mp4": ("m4a", 30 * 1024 * 1024),
        "audio/wav": ("wav", 30 * 1024 * 1024),
    },
}


def _opaque(value):
    return hmac.new(
        settings.MEDIA_PATH_HMAC_SECRET.encode(),
        str(value).encode(),
        hashlib.sha256,
    ).hexdigest()[:24]


def _object_key(user_id, conversation_id, media_type, extension):
    asset_id = uuid.uuid4()
    scope = (
        f"conversations/{_opaque(conversation_id)}"
        if conversation_id
        else f"users/{_opaque(user_id)}"
    )
    return str(
        PurePosixPath(
            "uploads",
            settings.ENVIRONMENT,
            scope,
            media_type,
            str(asset_id)[:2],
            f"{asset_id}.{extension}",
        )
    )


@transaction.atomic
def create_presigned_upload(*, user, media_type, content_type, size, conversation_id=None):
    enforce_rate_limit("upload-user", user.id, limit=30, period_seconds=3600)
    if media_type not in MEDIA_RULES or content_type not in MEDIA_RULES[media_type]:
        raise ValidationError("Type de média ou type MIME non autorisé.")
    extension, maximum = MEDIA_RULES[media_type][content_type]
    if size <= 0 or size > maximum:
        raise ValidationError(f"La taille doit être comprise entre 1 et {maximum} octets.")
    if conversation_id and not Membership.objects.filter(
        conversation_id=conversation_id,
        utilisateur=user,
    ).exists():
        raise PermissionDenied("Conversation inaccessible.")

    key = _object_key(user.id, conversation_id, media_type, extension)
    asset = MediaAsset.objects.create(
        utilisateur=user,
        conversation_id=conversation_id,
        type=media_type,
        source_object_key=key,
        content_type=content_type,
        taille_octets=size,
    )
    if getattr(settings, "MEDIA_USE_FAKE_PRESIGN", False):
        upload = {"url": "https://storage.example.test/upload", "fields": {"key": key}}
    else:
        upload = s3_client().generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, maximum],
            ],
            ExpiresIn=settings.AWS_S3_PRESIGNED_EXPIRY,
        )
    return asset, upload


@transaction.atomic
def complete_upload(*, user, asset_id):
    try:
        asset = MediaAsset.objects.select_for_update().get(pk=asset_id)
    except MediaAsset.DoesNotExist as exc:
        raise NotFound("Média introuvable.") from exc
    if asset.utilisateur_id != user.id:
        raise PermissionDenied("Média inaccessible.")
    if asset.statut != MediaAsset.Status.EN_ATTENTE:
        return asset, False

    if not getattr(settings, "MEDIA_USE_FAKE_PRESIGN", False):
        metadata = s3_client().head_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=asset.source_object_key,
        )
        actual_size = metadata["ContentLength"]
        actual_type = metadata.get("ContentType", "").split(";", 1)[0]
        _, maximum = MEDIA_RULES[asset.type][asset.content_type]
        if actual_size <= 0 or actual_size > maximum or actual_type != asset.content_type:
            raise ValidationError("Le fichier uploadé ne correspond pas à la demande signée.")

    asset.statut = MediaAsset.Status.UPLOADE
    asset.save(update_fields=["statut", "date_maj"])
    from .tasks import process_media_task

    transaction.on_commit(lambda: process_media_task.delay(asset.id))
    return asset, True


def serialize_asset(asset):
    output_key = asset.output_object_key or asset.source_object_key
    return {
        "id": asset.id,
        "type": asset.type,
        "status": asset.statut,
        "download_url": presigned_read_url(object_reference(output_key)),
        "thumbnail_url": (
            presigned_read_url(object_reference(asset.thumbnail_object_key)) if asset.thumbnail_object_key else None
        ),
        "duration": asset.duree,
    }
