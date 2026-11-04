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

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=300)
    link = models.CharField(max_length=200, blank=True)
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created"]
    def __str__(self): return f"{self.user}: {self.title}"

class Banner(models.Model):
    title = models.CharField(max_length=100)
    text = models.CharField("Short text (optional)", max_length=200, blank=True)
    image = models.ImageField(upload_to="banners/", validators=[max_5mb],
                              help_text="Best size 1600 x 400 pixels (wide, 4:1), JPG or PNG, under 5 MB. "
                                        "Any other size is cropped to fit automatically.")
    link = models.CharField(max_length=200, blank=True, help_text="Where a click goes, e.g. #book  /shop/  /connection/apply/")
    order = models.PositiveSmallIntegerField(default=0, help_text="Smaller number shows first")
    active = models.BooleanField(default=True, help_text="Untick to hide")
    created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["order", "-created"]
    def __str__(self): return self.title

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            img = ImageOps.exif_transpose(Image.open(self.image)).convert("RGB")
            img = ImageOps.fit(img, (1600, 400), method=Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            name = os.path.splitext(os.path.basename(self.image.name))[0] + ".jpg"
            self.image.save(name, ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)