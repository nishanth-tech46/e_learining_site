from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    phone_number = models.CharField(max_length=15, blank=False, null=False, unique=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    ambition = models.TextField(blank=True, help_text='User\'s career goals or ambitions')
    hobbies = models.TextField(blank=True, help_text='User\'s hobbies (comma-separated)')
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username


class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ('email', 'Email'),
        ('phone', 'Phone'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.save()
        return self.otp_code
    
    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=10)
    
    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"


# Payment model removed - access now controlled by admin enrollment
