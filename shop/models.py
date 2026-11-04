import os
import uuid
from io import BytesIO
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models, transaction
from PIL import Image, ImageOps

def max_5mb(f):
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be smaller than 5 MB.")

class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=60, default="Accessories")
    description = models.CharField(max_length=250, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, validators=[max_5mb],
                              help_text="JPG or PNG, under 5 MB. It is resized to a 600x600 square automatically.")
    active = models.BooleanField(default=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        # Resize only when a new image has just been uploaded
        if self.image and not self.image._committed:
            img = ImageOps.exif_transpose(Image.open(self.image)).convert("RGB")
            img = ImageOps.pad(img, (600, 600), method=Image.LANCZOS, color=(255, 255, 255))
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            name = os.path.splitext(os.path.basename(self.image.name))[0] + ".jpg"
            self.image.save(name, ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS = [("awaiting", "Awaiting payment"), ("placed", "Order placed"), ("packed", "Packed"),
              ("shipped", "Out for delivery"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    METHODS = [("cod", "Cash on delivery"), ("online", "Online (Razorpay)")]
    PAYSTATUS = [("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("cod", "Pay on delivery")]
    order_no = models.CharField(max_length=14, unique=True, editable=False, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop_orders")
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=METHODS, default="cod")
    payment_status = models.CharField(max_length=10, choices=PAYSTATUS, default="pending")
    status = models.CharField(max_length=12, choices=STATUS, default="awaiting")
    gateway_order_id = models.CharField(max_length=60, blank=True)
    gateway_payment_id = models.CharField(max_length=60, blank=True)
    confirmed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created"]
    def __str__(self): return self.order_no

    def save(self, *a, **k):
        if not self.order_no: self.order_no = "AGS" + uuid.uuid4().hex[:8].upper()
        super().save(*a, **k)

    @transaction.atomic
    def confirm(self, payment_status):
        """Called when COD is chosen or online payment is verified."""
        if self.confirmed: return
        for it in self.items.select_related("product"):
            p = it.product
            p.stock = max(0, p.stock - it.qty)
            p.save(update_fields=["stock"])
        self.confirmed = True
        self.status = "placed"
        self.payment_status = payment_status
        self.save()
        self.events.create(status="placed", note="Order received.")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    qty = models.PositiveIntegerField()
    @property
    def subtotal(self): return self.price * self.qty

class TrackingEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=12, choices=Order.STATUS)
    note = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created"]