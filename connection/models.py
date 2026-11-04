import os
import uuid
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps
from gas.models import Cylinder
from .storage import private_storage

def _name(folder, filename):
    return f"{folder}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"

def front_path(instance, filename): return _name("aadhaar", filename)
def back_path(instance, filename): return _name("aadhaar", filename)
def photo_path(instance, filename): return _name("photos", filename)

class NewConnection(models.Model):
    TYPES = [("single", "Single cylinder"), ("double", "Double cylinder")]
    STATUS = [("submitted", "Submitted"), ("verifying", "Under verification"),
              ("approved", "Approved"), ("rejected", "Rejected")]
    application_no = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connections")
    name = models.CharField("Full name (as on Aadhaar)", max_length=80)
    father_name = models.CharField("Father / spouse name", max_length=80)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField("Address for the connection")
    pincode = models.CharField(max_length=6)
    connection_type = models.CharField(max_length=10, choices=TYPES, default="single")
    cylinder = models.ForeignKey(Cylinder, on_delete=models.PROTECT, verbose_name="Cylinder type")
    aadhaar_last4 = models.CharField("Last 4 digits of Aadhaar", max_length=4)
    aadhaar_front = models.FileField("Aadhaar card (front)", upload_to=front_path, storage=private_storage)
    aadhaar_back = models.FileField("Aadhaar card (back, optional)", upload_to=back_path, storage=private_storage, blank=True)
    photo = models.ImageField("Passport size photo", upload_to=photo_path, storage=private_storage)
    status = models.CharField(max_length=10, choices=STATUS, default="submitted")
    remarks = models.CharField("Remarks for the customer", max_length=250, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "new connection application"

    def __str__(self): return f"{self.application_no} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.application_no:
            self.application_no = "NC" + uuid.uuid4().hex[:8].upper()
        # Resize a newly uploaded photo to 400 x 500 pixels
        if self.photo and not self.photo._committed:
            img = ImageOps.exif_transpose(Image.open(self.photo)).convert("RGB")
            img = ImageOps.fit(img, (400, 500), method=Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            self.photo.save("photo.jpg", ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)