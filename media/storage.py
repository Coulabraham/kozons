import boto3
from botocore.config import Config
from django.conf import settings
from urllib.parse import urlparse


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        config=Config(s3={"addressing_style": settings.AWS_S3_ADDRESSING_STYLE}),
    )


def object_reference(key):
    return f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{key}"


def presigned_read_url(reference):
    """Return a short-lived browser URL while keeping durable S3 references in PostgreSQL."""
    if not reference or not reference.startswith("s3://"):
        return reference
    parsed = urlparse(reference)
    if parsed.netloc != settings.AWS_STORAGE_BUCKET_NAME:
        return None
    key = parsed.path.lstrip("/")
    if getattr(settings, "MEDIA_USE_FAKE_PRESIGN", False):
        return f"https://storage.example.test/{key}"
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.AWS_S3_PRESIGNED_EXPIRY,
    )
