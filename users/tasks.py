from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command
from requests import RequestException

from .sms import get_sms_provider


@shared_task(
    autoretry_for=(OSError, RequestException),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=4,
)
def send_otp_task(channel, destination, code):
    if channel == "sms":
        get_sms_provider().send_otp(destination, code)
        return
    send_mail(
        subject="Votre code Kozons",
        message=f"Votre code de vérification Kozons est {code}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destination],
        fail_silently=False,
    )


@shared_task
def purge_expired_jwt_tokens():
    call_command("flushexpiredtokens")
