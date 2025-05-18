from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserProfileView, VerifyOtpView

urlpatterns = [
    path('users/register/', UserRegistrationView.as_view(), name='user_register'),
    path('users/login/', UserLoginView.as_view(), name='user_login'),
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
    path('users/VerifyOtpView/', VerifyOtpView.as_view(), name='verify')
]