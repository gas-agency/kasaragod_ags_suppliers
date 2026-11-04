import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image
from .models import NewConnection
from gas.models import Cylinder

MAX = 5 * 1024 * 1024

def _check_file(f, allow_pdf):
    if not f or not hasattr(f, "size"):
        return f
    if f.size > MAX:
        raise ValidationError("File must be smaller than 5 MB.")
    head = f.read(8); f.seek(0)
    if head.startswith(b"%PDF"):
        if not allow_pdf:
            raise ValidationError("Upload a JPG or PNG image.")
        return f
    try:
        img = Image.open(f); fmt = img.format; img.verify(); f.seek(0)
    except Exception:
        raise ValidationError("Upload a clear JPG or PNG image" + (" or a PDF." if allow_pdf else "."))
    if fmt not in ("JPEG", "PNG"):
        raise ValidationError("Only JPG or PNG images are allowed.")
    return f

class ApplicationForm(forms.ModelForm):
    consent = forms.BooleanField(
        label="I confirm these details are correct and I agree to share my Aadhaar card and photo with "
              f"{settings.AGENCY['name']} only for KYC verification of my new gas connection.")

    class Meta:
        model = NewConnection
        fields = ["name", "father_name", "phone", "email", "address", "pincode", "connection_type",
                  "cylinder", "aadhaar_last4", "aadhaar_front", "aadhaar_back", "photo"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "aadhaar_front": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.pdf"}),
            "aadhaar_back": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.pdf"}),
            "photo": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png"}),
        }

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields["cylinder"].queryset = Cylinder.objects.filter(available=True)

    def clean_phone(self):
        p = "".join(c for c in self.cleaned_data["phone"] if c.isdigit())[-10:]
        if len(p) != 10: raise ValidationError("Enter a 10-digit mobile number.")
        return p

    def clean_pincode(self):
        p = self.cleaned_data["pincode"].strip()
        if not (p.isdigit() and len(p) == 6): raise ValidationError("Enter a 6-digit pincode.")
        return p

    def clean_aadhaar_last4(self):
        a = self.cleaned_data["aadhaar_last4"].strip()
        if not (a.isdigit() and len(a) == 4): raise ValidationError("Enter exactly 4 digits.")
        return a

    def clean_aadhaar_front(self): return _check_file(self.cleaned_data.get("aadhaar_front"), True)
    def clean_aadhaar_back(self): return _check_file(self.cleaned_data.get("aadhaar_back"), True)
    def clean_photo(self): return _check_file(self.cleaned_data.get("photo"), False)