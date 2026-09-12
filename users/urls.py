from django.urls import path

from .views import ChangePasswordView, LoginView, LogoutAllView, LogoutView, RefreshView, RegisterView, ResendOTPView, VerifyOTPView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllView.as_view(), name="logout-all"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
]
