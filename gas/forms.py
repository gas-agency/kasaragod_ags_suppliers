from django import forms
from consumers.models import Consumer
from .models import Booking, Enquiry

def needs_consumer(cylinder):
    """14.2 kg cylinders must match a consumer in the list."""
    return bool(cylinder) and "14.2" in cylinder.weight.replace(" ", "")

def _digits10(s):
    return "".join(c for c in str(s or "") if c.isdigit())[-10:]

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["name", "phone", "consumer_no", "cylinder", "quantity", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *a, user=None, **k):
        super().__init__(*a, **k)
        self.user = user if user is not None and user.is_authenticated else None
        self.consumer = None
        self.fields["cylinder"].queryset = self.fields["cylinder"].queryset.filter(available=True)
        self.fields["consumer_no"].help_text = "Required for 14.2 kg cylinders. Use your gas connection consumer number."

    def clean_phone(self):
        p = _digits10(self.cleaned_data["phone"])
        if len(p) != 10: raise forms.ValidationError("Enter a 10-digit mobile number.")
        return p

    def clean(self):
        d = super().clean()
        if not needs_consumer(d.get("cylinder")):
            return d
        no = (d.get("consumer_no") or "").strip()
        if not no:
            self.add_error("consumer_no", "Consumer number is required for 14.2 kg cylinders.")
            return d
        c = Consumer.objects.filter(consumer_no__iexact=no, active=True).first()
        if not c:
            self.add_error("consumer_no", "We could not find this consumer number. Please check it or call us.")
            return d
        registered = _digits10(c.phone)
        linked = bool(self.user) and c.user_id == self.user.id
        if registered and d.get("phone") and d["phone"] != registered and not linked:
            self.add_error("phone", "Enter the mobile number registered with this consumer number.")
            return d
        self.consumer = c
        d["consumer_no"] = c.consumer_no
        return d

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ["name", "phone", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}