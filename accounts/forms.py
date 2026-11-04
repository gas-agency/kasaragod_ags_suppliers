from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
User = get_user_model()

class _BaseSignup(UserCreationForm):
    role = "customer"
    first_name = forms.CharField(label="Full name", max_length=80)
    phone = forms.CharField(max_length=15)
    class Meta:
        model = User
        fields = ("username", "first_name", "email", "phone")
    def clean_phone(self):
        p = "".join(c for c in self.cleaned_data["phone"] if c.isdigit())[-10:]
        if len(p) != 10: raise forms.ValidationError("Enter a 10-digit mobile number.")
        return p
    def save(self, commit=True):
        user = super().save(commit)
        Profile.objects.update_or_create(user=user, defaults={"role": self.role, "phone": self.cleaned_data["phone"]})
        return user

class CustomerSignupForm(_BaseSignup):
    role = "customer"

class StaffCreateForm(_BaseSignup):
    role = "staff"
    