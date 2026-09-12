import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from celery import shared_task
from django.conf import settings

from .models import MediaAsset
from .security import PermanentMediaValidationError, scan_file, validate_file_signature
from .storage import s3_client


def _processed_key(source_key, suffix, extension):
    source = PurePosixPath(source_key)
    name = f"{source.stem}{suffix}.{extension}"
    parts = list(source.parts)
    parts[0] = "processed"
    return str(PurePosixPath(*parts[:-1], name))


def _run(command):
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=12 * 60,
    )


@shared_task(bind=True, max_retries=3)
def process_media_task(self, asset_id):
    try:
        asset = MediaAsset.objects.get(pk=asset_id)
    except MediaAsset.DoesNotExist:
        return
    if asset.statut == MediaAsset.Status.PRET:
        return
    asset.statut = MediaAsset.Status.TRAITEMENT
    asset.erreur = None
    asset.save(update_fields=["statut", "erreur", "date_maj"])
    client = s3_client()
    try:
        with tempfile.TemporaryDirectory(prefix="kozons-media-") as temp_dir:
            temp = Path(temp_dir)
            source = temp / "source"
            client.download_file(settings.AWS_STORAGE_BUCKET_NAME, asset.source_object_key, str(source))
            validate_file_signature(source, asset.content_type)
            scan_file(source)

            if asset.type == MediaAsset.Type.IMAGE:
                asset.output_object_key = asset.source_object_key
                asset.statut = MediaAsset.Status.PRET
                asset.save(update_fields=["output_object_key", "statut", "date_maj"])
                return

            if asset.type == MediaAsset.Type.VIDEO:
                output = temp / "video.mp4"
                thumbnail = temp / "thumbnail.jpg"
                _run(
                    [
                        settings.FFMPEG_BINARY,
                        "-y",
                        "-i",
                        str(source),
                        "-vf",
                        "scale=w='min(1280,iw)':h=-2",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "medium",
                        "-crf",
                        "27",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "96k",
                        "-movflags",
                        "+faststart",
                        str(output),
                    ]
                )
                _run(
                    [
                        settings.FFMPEG_BINARY,
                        "-y",
                        "-ss",
                        "1",
                        "-i",
                        str(source),
                        "-frames:v",
                        "1",
                        "-vf",
                        "scale=480:-2",
                        str(thumbnail),
                    ]
                )
                output_key = _processed_key(asset.source_object_key, "", "mp4")
                thumbnail_key = _processed_key(asset.source_object_key, "-thumbnail", "jpg")
                client.upload_file(
                    str(output),
                    settings.AWS_STORAGE_BUCKET_NAME,
                    output_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
                client.upload_file(
                    str(thumbnail),
                    settings.AWS_STORAGE_BUCKET_NAME,
                    thumbnail_key,
                    ExtraArgs={"ContentType": "image/jpeg"},
                )
                asset.thumbnail_object_key = thumbnail_key
            else:
                output = temp / "voice.ogg"
                _run(
                    [
                        settings.FFMPEG_BINARY,
                        "-y",
                        "-i",
                        str(source),
                        "-vn",
                        "-c:a",
                        "libopus",
                        "-b:a",
                        "48k",
                        "-ac",
                        "1",
                        str(output),
                    ]
                )
                output_key = _processed_key(asset.source_object_key, "", "ogg")
                client.upload_file(
                    str(output),
                    settings.AWS_STORAGE_BUCKET_NAME,
                    output_key,
                    ExtraArgs={"ContentType": "audio/ogg"},
                )

            asset.output_object_key = output_key
            asset.statut = MediaAsset.Status.PRET
            asset.save(
                update_fields=[
                    "output_object_key",
                    "thumbnail_object_key",
                    "statut",
                    "date_maj",
                ]
            )
    except PermanentMediaValidationError as exc:
        try:
            client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=asset.source_object_key,
            )
        except Exception:
            pass
        asset.statut = MediaAsset.Status.ECHEC
        asset.erreur = str(exc)[:2000]
        asset.save(update_fields=["statut", "erreur", "date_maj"])
        return
    except Exception as exc:
        asset.statut = MediaAsset.Status.ECHEC
        asset.erreur = str(exc)[:2000]
        asset.save(update_fields=["statut", "erreur", "date_maj"])
        raise self.retry(exc=exc, countdown=min(60 * (2**self.request.retries), 600))
