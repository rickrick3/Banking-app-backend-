from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    national_id = models.ImageField(upload_to='ids/', blank=True, null=True)
    national_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)


    def __str__(self):
        return self.username
