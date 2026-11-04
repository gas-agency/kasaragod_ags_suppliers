from django import forms

class CheckoutForm(forms.Form):
    name = forms.CharField(label="Full name", max_length=80)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(label="Delivery address", widget=forms.Textarea(attrs={"rows": 3}))
    payment_method = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(self, *a, online=False, **k):
        super().__init__(*a, **k)
        choices = [("cod", "Cash on delivery")]
        if online: choices.append(("online", "Pay online (UPI / card / net banking)"))
        self.fields["payment_method"].choices = choices
        self.fields["payment_method"].initial = "cod"

    def clean_phone(self):
        p = "".join(c for c in self.cleaned_data["phone"] if c.isdigit())[-10:]
        if len(p) != 10: raise forms.ValidationError("Enter a 10-digit mobile number.")
        return p