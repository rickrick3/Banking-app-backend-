from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from .models import User
from .serializer import UserSerializer, UserLoginSerializer
import jwt
import requests
import datetime
import os

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Notify account service to create a default account for this user
            try:
                account_service_url = os.getenv('ACCOUNT_SERVICE_URL', 'http://account-service:8002')
                requests.post(
                    f"{account_service_url}/api/accounts/create/",
                    json={"user_id": str(user.id), "username": user.username}
                )
            except Exception as e:
                # Log the error, but don't fail registration
                print(f"Error notifying account service: {e}")

            return Response(
                {"message": "User registered successfully", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user:
                # Generate JWT token
                payload = {
                    'user_id': str(user.id),
                    'username': user.username,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
                }
                token = jwt.encode(payload, os.getenv('SECRET_KEY', 'your-secret-key-here'), algorithm='HS256')

                return Response({
                    "message": "Login successful",
                    "token": token,
                    "user": UserSerializer(user).data
                })
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# user-service/users/urls.py
from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserProfileView

urlpatterns = [
    path('users/register/', UserRegistrationView.as_view(), name='user_register'),
    path('users/login/', UserLoginView.as_view(), name='user_login'),
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
]