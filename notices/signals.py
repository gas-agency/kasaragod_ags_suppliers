from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from connection.models import NewConnection
from gas.models import Booking
from .utils import notify

AGENCY = lambda: settings.AGENCY["name"]

BOOKING_MSG = {
    "confirmed": ("Booking confirmed", "Your booking #{id} is confirmed. Our team will deliver your cylinder soon."),
    "delivered": ("Cylinder delivered", "Your booking #{id} has been delivered. Thank you for choosing {agency}."),
    "cancelled": ("Booking cancelled", "Your booking #{id} was cancelled. Please call us if this is a mistake."),
}
NC_MSG = {
    "verifying": ("Documents under verification", "We are verifying the documents for application {no}."),
    "approved": ("New connection approved", "Good news! Your application {no} is approved. We will contact you to complete the connection."),
    "rejected": ("Application needs attention", "Your application {no} could not be approved. {remarks}"),
}

# ----- Gas bookings -----
@receiver(pre_save, sender=Booking)
def booking_before(sender, instance, **kw):
    instance._old = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first() if instance.pk else None

@receiver(post_save, sender=Booking)
def booking_after(sender, instance, created, **kw):
    if not instance.customer_id: return
    link = reverse("customer_home")
    if created:
        notify(instance.customer, "Booking received",
               f"Booking #{instance.pk} received for {instance.cylinder} x {instance.quantity}. "
               f"We will call you on {instance.phone} to confirm delivery.", link)
    elif getattr(instance, "_old", None) != instance.status and instance.status in BOOKING_MSG:
        t, m = BOOKING_MSG[instance.status]
        notify(instance.customer, t, m.format(id=instance.pk, agency=AGENCY()), link)

# ----- New connection applications -----
@receiver(pre_save, sender=NewConnection)
def nc_before(sender, instance, **kw):
    instance._old = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first() if instance.pk else None

@receiver(post_save, sender=NewConnection)
def nc_after(sender, instance, created, **kw):
    link = reverse("nc_detail", args=[instance.application_no])
    if created:
        notify(instance.user, "Application received",
               f"Your new connection application {instance.application_no} is received. "
               f"We will verify your documents and update you here.", link)
    elif getattr(instance, "_old", None) != instance.status and instance.status in NC_MSG:
        t, m = NC_MSG[instance.status]
        notify(instance.user, t, m.format(no=instance.application_no,
               remarks=("Reason: " + instance.remarks) if instance.remarks else "Please contact us."), link)