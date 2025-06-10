from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_expired(self):
        """Check if verification code is expired (24 hours)"""
        return timezone.now() > self.created_at + timedelta(hours=24)
    
    def __str__(self):
        return f"Verification for {self.user.email}"
    
    class Meta:
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"



class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_code = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    def is_expired(self):
        """Check if reset code is expired (1 hour)"""
        return timezone.now() > self.created_at + timedelta(hours=1)
    
    def __str__(self):
        return f"Password reset for {self.user.email}"
    
    class Meta:
        verbose_name = "Password Reset"
        verbose_name_plural = "Password Resets"