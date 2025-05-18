
from rest_framework import status, parsers
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
import random

def generate_otp():
    return str(random.randint(100000, 999999))

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            otp = generate_otp()
            user.otp_code = otp
            user.save()

            # Here you would send the OTP via SMS or email

            try:
                account_service_url = os.getenv('ACCOUNT_SERVICE_URL', 'http://account-service:8002')
                requests.post(
                    f"{account_service_url}/api/accounts/create/",
                    json={"user_id": str(user.id), "username": user.username}
                )
            except Exception as e:
                print(f"Error notifying account service: {e}")

            return Response(
                {"message": "User registered successfully", "user_id": user.id, "otp": otp},
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
                if not user.is_verified:
                    return Response({"message": "Account not verified"}, status=status.HTTP_403_FORBIDDEN)

                payload = {
                    'user_id': str(user.id),
                    'username': user.username,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
                }
                token = jwt.encode(payload, os.getenv('SECRET_KEY', 'django-insecure-&0=h=%@kffjt2m(co=$ekjq7q*!84h2w0ooes$w72duwqm=&kh'), algorithm='HS256')

                return Response({
                    "message": "Login successful",
                    "token": token,
                    "user": UserSerializer(user).data
                })
            else:
                return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        if user.otp_code == otp:
            user.is_verified = True
            user.otp_code = ''
            user.save()
            return Response({'message': 'Account verified successfully'})
        else:
            return Response({'error': 'Invalid OTP'}, status=400)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
