from django.conf import settings
from django.db import models

class Consumer(models.Model):
    consumer_no = models.CharField("Consumer number", max_length=30, unique=True)
    lpg_id = models.CharField("LPG ID", max_length=30, blank=True)
    name = models.CharField(max_length=120)
    father_name = models.CharField("Father / spouse name", max_length=120, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    category = models.CharField(max_length=60, blank=True, help_text="e.g. Domestic, Commercial")
    connection_type = models.CharField(max_length=60, blank=True, help_text="e.g. Single, Double")
    cylinder_type = models.CharField(max_length=60, blank=True, help_text="e.g. 14.2 kg")
    connection_date = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=250, blank=True)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="consumers", help_text="Website account linked to this consumer")
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return f"{self.consumer_no} - {self.name}"