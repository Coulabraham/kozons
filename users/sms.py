import logging
from abc import ABC, abstractmethod

import requests
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class SMSProvider(ABC):
    @abstractmethod
    def send_otp(self, destination, code):
        raise NotImplementedError


class ConsoleSMSProvider(SMSProvider):
    def send_otp(self, destination, code):
        logger.warning("OTP de développement pour %s : %s", destination, code)


class TwilioSMSProvider(SMSProvider):
    def send_otp(self, destination, code):
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        )
        response = requests.post(
            url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={
                "From": settings.TWILIO_FROM_NUMBER,
                "To": destination,
                "Body": f"Votre code Kozons est {code}. Il expire bientôt.",
            },
            timeout=10,
        )
        response.raise_for_status()


class AfricasTalkingSMSProvider(SMSProvider):
    def send_otp(self, destination, code):
        data = {
            "username": settings.AFRICASTALKING_USERNAME,
            "to": destination,
            "message": f"Votre code Kozons est {code}. Il expire bientôt.",
        }
        if settings.AFRICASTALKING_SENDER_ID:
            data["from"] = settings.AFRICASTALKING_SENDER_ID
        response = requests.post(
            "https://api.africastalking.com/version1/messaging",
            headers={"apiKey": settings.AFRICASTALKING_API_KEY, "Accept": "application/json"},
            data=data,
            timeout=10,
        )
        response.raise_for_status()


def get_sms_provider():
    provider_class = import_string(settings.SMS_PROVIDER)
    return provider_class()
