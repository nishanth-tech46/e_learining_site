from django.contrib import admin
from .models import User, OTP


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'phone_number', 'user_type', 'email_verified', 'phone_verified']
    list_filter = ['user_type', 'email_verified', 'phone_verified']
    search_fields = ['username', 'email', 'phone_number']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_type', 'otp_code', 'created_at', 'is_used']
    list_filter = ['otp_type', 'is_used']
    search_fields = ['user__username', 'otp_code']


# Payment admin removed - access now controlled by admin enrollment
