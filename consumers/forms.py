import os
from django import forms

class ImportForm(forms.Form):
    file = forms.FileField(label="Excel (.xlsx) or CSV file")
    preview = forms.BooleanField(required=False, label="Preview only (check the file without saving)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if os.path.splitext(f.name)[1].lower() not in (".xlsx", ".csv"):
            raise forms.ValidationError("Upload an .xlsx or .csv file. If you have .xls, open it and save as .xlsx.")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File must be smaller than 5 MB.")
        return f