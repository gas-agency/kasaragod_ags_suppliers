import os
from io import BytesIO
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

def max_5mb(f):
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be smaller than 5 MB.")

class Slide(models.Model):
    COLORS = [("blue", "Blue"), ("navy", "Dark blue"), ("red", "Red"), ("dark", "Charcoal")]
    title = models.CharField(max_length=100)
    text = models.CharField("Text", max_length=220, blank=True)
    button_text = models.CharField(max_length=40, blank=True, help_text="Leave empty for no button")
    button_link = models.CharField(max_length=200, blank=True, default="#book",
                                   help_text="Examples: #book  #cylinders  #contact  /shop/")
    image = models.ImageField(upload_to="slides/", blank=True, validators=[max_5mb],
                              help_text="Best size 1600 x 640 pixels, under 5 MB. Cropped to fit automatically.")
    color = models.CharField("Background colour", max_length=10, choices=COLORS, default="blue",
                             help_text="Used when no image is uploaded")
    order = models.PositiveSmallIntegerField(default=0, help_text="Smaller number shows first")
    active = models.BooleanField(default=True, help_text="Untick to hide this slide")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "carousel slide"
        verbose_name_plural = "carousel slides"

    def __str__(self): return self.title

    def save(self, *args, **kwargs):
        # Crop every new upload to the same 1600 x 640 size
        if self.image and not self.image._committed:
            img = ImageOps.exif_transpose(Image.open(self.image)).convert("RGB")
            img = ImageOps.fit(img, (1600, 640), method=Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            name = os.path.splitext(os.path.basename(self.image.name))[0] + ".jpg"
            self.image.save(name, ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)