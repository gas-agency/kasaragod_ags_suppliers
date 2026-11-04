

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Banner, Notification

@login_required
def notifications(request):
    qs = Notification.objects.filter(user=request.user)
    items = list(qs[:50])
    qs.filter(read=False).update(read=True)
    return render(request, "notices/notifications.html", {"items": items})

def offers(request):
    return render(request, "notices/offers.html", {"banners": Banner.objects.filter(active=True)})