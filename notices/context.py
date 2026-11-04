from .models import Notification

def unread(request):
    u = getattr(request, "user", None)
    if u is not None and u.is_authenticated:
        return {"unread_count": Notification.objects.filter(user=u, read=False).count()}
    return {"unread_count": 0}