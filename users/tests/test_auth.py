import pytest
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from users.models import OTPVerification, User


@pytest.mark.django_db
def test_registration_with_email_sends_the_otp(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = APIClient().post(
            "/api/auth/register/",
            {
                "email": "nouveau@example.test",
                "password": "MotDePasseSolide!42",
                "nom_affichage": "Nouveau membre",
            },
            format="json",
        )

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["nouveau@example.test"]
    assert "000000" in mail.outbox[0].body


@pytest.mark.django_db
def test_register_verify_and_login_with_phone():
    client = APIClient()
    registration = client.post(
        "/api/auth/register/",
        {
            "telephone": "+221771234567",
            "password": "MotDePasseSolide!42",
            "nom_affichage": "Awa Ndiaye",
        },
        format="json",
    )
    assert registration.status_code == 201
    user = User.objects.get(telephone="+221771234567")
    assert user.check_password("MotDePasseSolide!42")
    assert not user.is_active

    invalid = client.post(
        "/api/auth/verify-otp/",
        {"identifier": "+221771234567", "code": "111111"},
        format="json",
    )
    assert invalid.status_code == 400
    assert OTPVerification.objects.get(user=user).attempts == 1

    verification = client.post(
        "/api/auth/verify-otp/",
        {"identifier": "+221771234567", "code": "000000"},
        format="json",
    )
    assert verification.status_code == 200
    user.refresh_from_db()
    assert user.is_active

    login = client.post(
        "/api/auth/login/",
        {"identifier": "+221771234567", "password": "MotDePasseSolide!42"},
        format="json",
    )
    assert login.status_code == 200
    assert login.data["access"]
    assert "refresh" not in login.data
    assert login.cookies["kozons_refresh"]["httponly"]

    refresh = client.post("/api/auth/refresh/", format="json")
    assert refresh.status_code == 200
    assert refresh.data["access"]


@pytest.mark.django_db
def test_logout_blacklists_refresh_token_and_clears_cookie():
    user = User.objects.create_user(
        email="awa@example.test", password="MotDePasseSolide!42", nom_affichage="Awa",
        is_active=True, statut="actif",
    )
    client = APIClient()
    login = client.post("/api/auth/login/", {"identifier": user.email, "password": "MotDePasseSolide!42"}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    response = client.post("/api/auth/logout/", format="json")
    assert response.status_code == 204
    assert BlacklistedToken.objects.filter(token__user=user).exists()
    assert response.cookies["kozons_refresh"]["max-age"] == 0


@pytest.mark.django_db
def test_logout_all_revokes_already_issued_access_token():
    user = User.objects.create_user(
        email="all@example.test", password="MotDePasseSolide!42", nom_affichage="Toutes sessions",
        is_active=True, statut="actif",
    )
    client = APIClient()
    login = client.post("/api/auth/login/", {"identifier": user.email, "password": "MotDePasseSolide!42"}, format="json")
    access = login.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert client.post("/api/auth/logout-all/", format="json").status_code == 204
    assert client.get("/api/profile/").status_code == 401


@pytest.mark.django_db
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.Argon2PasswordHasher"])
def test_argon2_is_supported_for_password_hashing():
    user = User.objects.create_user(email="argon@example.test", password="MotDePasseSolide!42", nom_affichage="Argon")
    assert user.password.startswith("argon2$")
    assert user.check_password("MotDePasseSolide!42")


@pytest.mark.django_db
def test_registration_requires_phone_or_email():
    response = APIClient().post(
        "/api/auth/register/",
        {"password": "MotDePasseSolide!42", "nom_affichage": "Sans Identifiant"},
        format="json",
    )
    assert response.status_code == 400


def test_api_security_headers_are_present():
    response = APIClient().get("/api/health/")
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in response["Content-Security-Policy"]
