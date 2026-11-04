from django.conf import settings
from django.db import models

class Profile(models.Model):
    ROLES = [("customer", "Customer"), ("staff", "Staff"), ("manager", "Manager")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLES, default="customer")
    phone = models.CharField(max_length=15, blank=True)
    def __str__(self): return f"{self.user} ({self.role})"