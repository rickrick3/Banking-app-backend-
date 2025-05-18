from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, VerificationOTP, IDVerificationRequest

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'confirm_password', 'phone_number']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'address', 'id_number']

class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)

class IDVerificationSerializer(serializers.ModelSerializer):
    id_front = serializers.ImageField(required=True)
    id_back = serializers.ImageField(required=True)
    id_number = serializers.CharField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['id_front', 'id_back', 'id_number']

class IDVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDVerificationRequest
        fields = ['status', 'rejection_reason', 'submitted_at', 'processed_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'phone_number', 'is_email_verified', 'is_id_verified']
        read_only_fields = ['is_email_verified', 'is_id_verified']
