import os
from io import BytesIO
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

def max_5mb(f):
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be smaller than 5 MB.")

class Cylinder(models.Model):
    name = models.CharField(max_length=60)
    weight = models.CharField(max_length=20, help_text="e.g. 14.2 kg")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    use = models.CharField(max_length=120, help_text="Who it is for")
    image = models.ImageField(upload_to="cylinders/", blank=True, validators=[max_5mb],
                              help_text="JPG or PNG, under 5 MB. Resized to a 600x600 square automatically.")
    available = models.BooleanField(default=True)
    def __str__(self): return f"{self.name} ({self.weight})"

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            img = ImageOps.exif_transpose(Image.open(self.image)).convert("RGB")
            img = ImageOps.pad(img, (600, 600), method=Image.LANCZOS, color=(255, 255, 255))
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            name = os.path.splitext(os.path.basename(self.image.name))[0] + ".jpg"
            self.image.save(name, ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)

class Booking(models.Model):
    STATUS = [("new", "New"), ("confirmed", "Confirmed"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    consumer_no = models.CharField("Consumer number", max_length=30, blank=True)
    cylinder = models.ForeignKey(Cylinder, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    address = models.TextField()
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="bookings")
    status = models.CharField(max_length=12, choices=STATUS, default="new")
    created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created"]
    def __str__(self): return f"#{self.pk} {self.name} - {self.cylinder}"

class Enquiry(models.Model):
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "enquiries"
    def __str__(self): return f"{self.name} ({self.phone})"