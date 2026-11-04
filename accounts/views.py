from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth import get_user_model, login
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from gas.models import Booking
from .forms import CustomerSignupForm, StaffCreateForm
from .models import Profile
from .utils import role_of, role_required
User = get_user_model()

def register(request):
    if request.user.is_authenticated: return redirect("dashboard")
    form = CustomerSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Account created. You are logged in.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})

@role_required("customer", "staff", "manager")
def dashboard(request):
       return redirect({"manager": "admin_dashboard", "staff": "staff_home"}.get(role_of(request.user), "customer_home"))

@role_required("customer", "staff", "manager")
def customer_home(request):
    return render(request, "accounts/customer.html", {"bookings": request.user.bookings.select_related("cylinder")})

@role_required("staff", "manager")
def staff_home(request):
    if request.method == "POST":
        b = get_object_or_404(Booking, pk=request.POST.get("booking"))
        status = request.POST.get("status")
        if status in dict(Booking.STATUS):
            b.status = status; b.save(update_fields=["status"])
            messages.success(request, f"Booking #{b.pk} marked {b.get_status_display()}.")
        return redirect(request.get_full_path())
    qs = Booking.objects.select_related("cylinder", "customer")
    f = request.GET.get("status")
    if f in dict(Booking.STATUS): qs = qs.filter(status=f)
    return render(request, "accounts/staff.html", {"bookings": qs[:100], "statuses": Booking.STATUS, "filter": f})

@role_required("manager")
def manager_home(request):
    counts = dict(Booking.objects.values_list("status").annotate(n=Count("id")))
    stats = [(label, counts.get(key, 0)) for key, label in Booking.STATUS]
    staff = Profile.objects.filter(role="staff").select_related("user")
    return render(request, "accounts/manager.html", {"stats": stats, "staff": staff,
        "customers": Profile.objects.filter(role="customer").count(), "total": sum(counts.values())})

@role_required("manager")
def staff_new(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        u = form.save(); messages.success(request, f"Staff account '{u.username}' created.")
        return redirect("manager_home")
    return render(request, "accounts/staff_form.html", {"form": form})

@role_required("manager")
@require_POST
def staff_toggle(request, pk):
    p = get_object_or_404(Profile, pk=pk, role="staff")
    p.user.is_active = not p.user.is_active; p.user.save(update_fields=["is_active"])
    messages.success(request, f"{p.user.username} is now {'active' if p.user.is_active else 'disabled'}.")
    return redirect("manager_home")

@require_POST
def keepalive(request):
    """The browser calls this while the person is active, to keep the session alive."""
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    return HttpResponse(status=204)