from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Profile

def role_of(user):
    """manager = superuser or Profile.role == manager; staff; customer."""
    if not user.is_authenticated: return None
    if user.is_superuser: return "manager"
    return Profile.objects.get_or_create(user=user)[0].role

def role_required(*roles):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapper(request, *a, **k):
            if role_of(request.user) not in roles: raise PermissionDenied
            return view(request, *a, **k)
        return wrapper
    return deco

def role_context(request):
    return {"role": role_of(request.user)}