from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import VerificationOTP, UserProfile, IDVerificationRequest
from .serializers import (
    UserRegistrationSerializer, 
    LoginSerializer, 
    VerifyOTPSerializer, 
    IDVerificationSerializer,
    IDVerificationStatusSerializer,
    UserSerializer
)
from .utils import generate_otp, calculate_otp_expiry, send_otp_email, validate_id_document

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Generate and send OTP
        otp = generate_otp()
        expiry = calculate_otp_expiry()
        VerificationOTP.objects.create(user=user, code=otp, expires_at=expiry)
        
        # Send email with OTP
        send_otp_email(user.email, otp)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Registration successful. Please verify your email with the OTP sent.'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Login successful'
        })

class ResendOTPView(APIView):
    def post(self, request):
        user = request.user
        
        # Check if already verified
        if user.is_email_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Invalidate any existing OTPs
        VerificationOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate and send new OTP
        otp = generate_otp()
        expiry = calculate_otp_expiry()
        VerificationOTP.objects.create(user=user, code=otp, expires_at=expiry)
        
        # Send email with OTP
        send_otp_email(user.email, otp)
        
        return Response({'message': 'OTP has been sent to your email'})

class VerifyEmailOTPView(APIView):
    def post(self, request):
        user = request.user
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if already verified
        if user.is_email_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate OTP
        otp_obj = VerificationOTP.objects.filter(
            user=user,
            code=serializer.validated_data['otp'],
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not otp_obj:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()
        
        # Mark email as verified
        user.is_email_verified = True
        user.save()
        
        return Response({'message': 'Email verification successful'})

class SubmitIDVerificationView(APIView):
    def post(self, request):
        user = request.user
        
        # Check if email is verified
        if not user.is_email_verified:
            return Response(
                {'error': 'Please verify your email before submitting ID verification'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if ID is already verified
        if user.is_id_verified:
            return Response(
                {'message': 'ID already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = IDVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        with transaction.atomic():
            # Save ID information to profile
            profile.id_front = serializer.validated_data['id_front']
            profile.id_back = serializer.validated_data['id_back']
            profile.id_number = serializer.validated_data['id_number']
            profile.save()
            
            # Validate ID documents (in a real-world scenario, this would likely be an async process)
            is_valid, message = validate_id_document(
                profile.id_front, 
                profile.id_back, 
                profile.id_number
            )
            
            # Create verification request
            verification_request = IDVerificationRequest.objects.create(
                user=user,
                status='approved' if is_valid else 'rejected',
                rejection_reason=None if is_valid else message,
                processed_at=timezone.now() if is_valid else None
            )
            
            # If valid, mark user as ID verified
            if is_valid:
                user.is_id_verified = True
                user.save()
            
            # Send email notification
            send_mail_subject = f"ID Verification {'Approved' if is_valid else 'Rejected'}"
            send_mail_message = f"Your ID verification has been {'approved' if is_valid else 'rejected'}. {'You can now perform transactions.' if is_valid else f'Reason: {message}'}"
            send_mail(send_mail_subject, send_mail_message, settings.EMAIL_HOST_USER, [user.email])
            
            return Response({
                'status': verification_request.status,
                'message': 'ID verification submitted successfully and ' + 
                           ('approved' if is_valid else f'rejected. Reason: {message}')
            })

class IDVerificationStatusView(generics.RetrieveAPIView):
    serializer_class = IDVerificationStatusSerializer
    
    def get_object(self):
        return get_object_or_404(IDVerificationRequest, user=self.request.user)

class UserAccountStatusView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
