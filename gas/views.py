from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import BookingForm, EnquiryForm
from .models import Cylinder

def _ctx(request, booking_form=None):
    initial = {}
    if request.user.is_authenticated:
        initial["name"] = request.user.get_full_name() or request.user.username
        p = getattr(request.user, "profile", None)
        if p: initial["phone"] = p.phone
        c = request.user.consumers.first()
        if c: initial["consumer_no"] = c.consumer_no
    return {"cylinders": Cylinder.objects.filter(available=True),
            "booking_form": booking_form or BookingForm(initial=initial, user=request.user),
            "enquiry_form": EnquiryForm()}

def _error_text(form):
    parts = []
    for field, errs in form.errors.items():
        prefix = "" if field == "__all__" else f"{form[field].label}: "
        parts.append(prefix + " ".join(errs))
    return " ".join(parts)

def home(request):
    return render(request, "home.html", _ctx(request))

def book(request):
    if request.method == "POST":
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            b = form.save(commit=False)
            if request.user.is_authenticated: b.customer = request.user
            b.save()
            msg = f"Booking #{b.pk} received. We will call you on {b.phone} to confirm delivery."
            if form.consumer: msg += f" Consumer {form.consumer.consumer_no} verified."
            messages.success(request, msg)
            return redirect("/#book")
        messages.error(request, "Your booking could not be completed. " + _error_text(form) +
                       " Please contact us and we will help you.")
        return redirect("/#contact")
    return redirect("/#book")

def enquiry(request):
    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Message sent. We will get back to you soon.", extra_tags="contact")
    return redirect("/#contact")