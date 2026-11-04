import mimetypes
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from accounts.utils import role_of, role_required
from .forms import ApplicationForm
from .models import NewConnection

def _can_view(user, app):
    return app.user_id == user.id or role_of(user) in ("staff", "manager")

@login_required
def apply(request):
    p = getattr(request.user, "profile", None)
    initial = {"name": request.user.get_full_name() or request.user.username,
               "phone": p.phone if p else "", "email": request.user.email}
    form = ApplicationForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        app = form.save(commit=False)
        app.user = request.user
        app.save()
        messages.success(request, f"Application {app.application_no} submitted. We will verify your documents and contact you.")
        return redirect("nc_detail", app.application_no)
    return render(request, "connection/apply.html", {"form": form})

@login_required
def my_applications(request):
    return render(request, "connection/list.html", {"apps": NewConnection.objects.filter(user=request.user)})

@login_required
def detail(request, application_no):
    app = get_object_or_404(NewConnection, application_no=application_no)
    if not _can_view(request.user, app): raise PermissionDenied
    return render(request, "connection/detail.html", {"a": app})

@login_required
def document(request, application_no, kind):
    app = get_object_or_404(NewConnection, application_no=application_no)
    if not _can_view(request.user, app): raise PermissionDenied
    f = {"photo": app.photo, "front": app.aadhaar_front, "back": app.aadhaar_back}.get(kind)
    if not f: raise Http404
    try:
        fh = f.open("rb")
    except FileNotFoundError:
        raise Http404
    resp = FileResponse(fh, content_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream")
    resp["Cache-Control"] = "private, no-store"
    resp["X-Content-Type-Options"] = "nosniff"
    return resp

@role_required("staff", "manager")
def manage(request):
    if request.method == "POST":
        app = get_object_or_404(NewConnection, pk=request.POST.get("app"))
        st = request.POST.get("status")
        if st in dict(NewConnection.STATUS):
            app.status = st
            app.remarks = request.POST.get("remarks", "").strip()[:250]
            app.save(update_fields=["status", "remarks", "updated"])
            messages.success(request, f"{app.application_no} updated to {app.get_status_display()}.")
        return redirect(request.get_full_path())
    qs = NewConnection.objects.select_related("cylinder")
    f = request.GET.get("status")
    if f in dict(NewConnection.STATUS): qs = qs.filter(status=f)
    return render(request, "connection/manage.html", {"apps": qs[:100], "statuses": NewConnection.STATUS})