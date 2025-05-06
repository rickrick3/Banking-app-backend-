from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Account, Transaction

class TransactionService:
    """Service class for handling banking transactions"""
    
    @staticmethod
    @transaction.atomic
    def deposit(account_id, amount, description=None):
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValidationError("Deposit amount must be positive")
                
            account = Account.objects.select_for_update().get(id=account_id, is_active=True)
            
            # Create transaction record
            txn = Transaction(
                from_account=account,
                transaction_type='DEPOSIT',
                amount=amount,
                description=description or "Deposit"
            )
            
            # Update account balance
            account.balance += amount
            account.save()
            
            # Mark transaction as completed
            txn.status = 'COMPLETED'
            txn.save()
            
            return txn
            
        except Account.DoesNotExist:
            raise ValidationError("Account not found or inactive")
        except Exception as e:
            raise ValidationError(f"Deposit failed: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def withdraw(account_id, amount, description=None):
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValidationError("Withdrawal amount must be positive")
                
            account = Account.objects.select_for_update().get(id=account_id, is_active=True)
            
            # Check sufficient funds
            if account.balance < amount:
                raise ValidationError("Insufficient funds for withdrawal")
            
            # Create transaction record
            txn = Transaction(
                from_account=account,
                transaction_type='WITHDRAWAL',
                amount=amount,
                description=description or "Withdrawal"
            )
            
            # Update account balance
            account.balance -= amount
            account.save()
            
            # Mark transaction as completed
            txn.status = 'COMPLETED'
            txn.save()
            
            return txn
            
        except Account.DoesNotExist:
            raise ValidationError("Account not found or inactive")
        except Exception as e:
            raise ValidationError(f"Withdrawal failed: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def transfer(from_account_id, to_account_id, amount, description=None):
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValidationError("Transfer amount must be positive")
                
            # Lock both accounts for update to prevent race conditions
            from_account = Account.objects.select_for_update().get(id=from_account_id, is_active=True)
            to_account = Account.objects.select_for_update().get(id=to_account_id, is_active=True)
            
            # Check sufficient funds
            if from_account.balance < amount:
                raise ValidationError("Insufficient funds for transfer")
            
            # Create transaction record
            txn = Transaction(
                from_account=from_account,
                to_account=to_account,
                transaction_type='TRANSFER',
                amount=amount,
                description=description or f"Transfer to {to_account.account_number}"
            )
            
            # Update account balances
            from_account.balance -= amount
            to_account.balance += amount
            
            from_account.save()
            to_account.save()
            
            # Mark transaction as completed
            txn.status = 'COMPLETED'
            txn.save()
            
            return txn
            
        except Account.DoesNotExist:
            raise ValidationError("One or both accounts not found or inactive")
        except Exception as e:
            raise ValidationError(f"Transfer failed: {str(e)}")
    
    @staticmethod
    def get_account_transactions(account_id, start_date=None, end_date=None, transaction_type=None):
        """
        Get transactions for a specific account with optional filters
        
        Args:
            account_id (int): ID of the account
            start_date (datetime, optional): Start date for filtering
            end_date (datetime, optional): End date for filtering
            transaction_type (str, optional): Type of transaction to filter by
            
        Returns:
            QuerySet: Filtered transactions
        """
        try:
            account = Account.objects.get(id=account_id)
            
            # All transactions related to this account (debits and credits)
            transactions = Transaction.objects.filter(
                models.Q(from_account=account) | models.Q(to_account=account)
            ).order_by('-timestamp')
            
            # Apply filters if specified
            if start_date:
                transactions = transactions.filter(timestamp__gte=start_date)
            if end_date:
                transactions = transactions.filter(timestamp__lte=end_date)
            if transaction_type:
                transactions = transactions.filter(transaction_type=transaction_type)
                
            return transactions
            
        except Account.DoesNotExist:
            raise ValidationError("Account not found")


# serializers.py
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