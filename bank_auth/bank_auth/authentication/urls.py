from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import (
    RegisterView,
    LoginView,
    ResendOTPView,
    VerifyEmailOTPView,
    SubmitIDVerificationView,
    IDVerificationStatusView,
    UserAccountStatusView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('verify-email/', VerifyEmailOTPView.as_view(), name='verify-email'),
    path('verify-id/', SubmitIDVerificationView.as_view(), name='verify-id'),
    path('id-status/', IDVerificationStatusView.as_view(), name='id-status'),
    path('account-status/', UserAccountStatusView.as_view(), name='account-status'),
]