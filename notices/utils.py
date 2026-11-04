from django.conf import settings
from django.core.mail import send_mail
from .models import Notification

def notify(user, title, message, link=""):
    Notification.objects.create(user=user, title=title, message=message[:300], link=link)
    if user.email:
        send_mail(title, f"{message}\n\n{settings.AGENCY['name']}\nPhone: {settings.AGENCY['phone']}",
                  settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)