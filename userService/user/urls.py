from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserProfileView

urlpatterns = [
    path('users/register/', UserRegistrationView.as_view(), name='user_register'),
    path('users/login/', UserLoginView.as_view(), name='user_login'),
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
]