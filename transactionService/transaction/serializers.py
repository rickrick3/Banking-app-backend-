from rest_framework import serializers
from .models import Account, Transaction

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'balance', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['balance', 'account_number']

class TransactionSerializer(serializers.ModelSerializer):
    from_account_number = serializers.CharField(source='from_account.account_number', read_only=True)
    to_account_number = serializers.CharField(source='to_account.account_number', read_only=True, required=False)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'from_account', 'from_account_number',
            'to_account', 'to_account_number', 'transaction_type',
            'amount', 'status', 'description', 'timestamp'
        ]
        read_only_fields = ['transaction_id', 'status', 'timestamp']