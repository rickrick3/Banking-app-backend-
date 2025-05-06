from django.db import models
import uuid
from decimal import Decimal

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('savings', 'Savings'),
        ('checking', 'Checking'),
        ('business', 'Business'),
    )
    
    ACCOUNT_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    )
    
    CURRENCIES = (
        ('USD', 'US Dollar'),
        ('XAF', 'Central Africa'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        # Add more currencies as needed
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='checking')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='XAF')
    status = models.CharField(max_length=10, choices=ACCOUNT_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.account_type}"
    
    class Meta:
        db_table = 'accounts'
