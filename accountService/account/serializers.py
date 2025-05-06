from rest_framework import serializers
from .models import Account
import random

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'user_id', 'account_number', 'account_type', 'balance', 'currency', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'account_number', 'balance', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Generate a unique account number
        while True:
            account_number = ''.join(random.choices('0123456789', k=10))
            if not Account.objects.filter(account_number=account_number).exists():
                break
        
        validated_data['account_number'] = account_number
        return super().create(validated_data)

class AccountCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    username = serializers.CharField(required=False)
    account_type = serializers.ChoiceField(choices=Account.ACCOUNT_TYPES, default='checking')
    currency = serializers.ChoiceField(choices=Account.CURRENCIES, default='XAF')

class TopUpSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    description = serializers.CharField(required=False)