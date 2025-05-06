from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('SAVINGS', 'Savings Account'),
        ('CHECKING', 'Checking Account'),
        ('INVESTMENT', 'Investment Account'),
    )
    
    account_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.account_type} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        # Generate unique account number if not set
        if not self.account_number:
            self.account_number = str(uuid.uuid4().int)[:10]
        super().save(*args, **kwargs)

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    transaction_id = models.CharField(max_length=50, unique=True)
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debits')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credits', null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    description = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate transaction ID if not set
        if not self.transaction_id:
            self.transaction_id = f"TXN-{str(uuid.uuid4())[:8]}-{timezone.now().strftime('%Y%m%d')}"
        super().save(*args, **kwargs)

    def clean(self):
        # Validate transaction based on type
        if self.transaction_type == 'TRANSFER' and not self.to_account:
            raise ValidationError("Transfer transactions require a destination account")
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero")
        
        # For withdrawal and transfer, ensure sufficient funds
        if self.transaction_type in ['WITHDRAWAL', 'TRANSFER']:
            if self.from_account.balance < self.amount:
                raise ValidationError("Insufficient funds for this transaction")
