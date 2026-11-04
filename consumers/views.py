from django.http import HttpResponse
from openpyxl import Workbook
from accounts.utils import role_required

HEADERS = ["Consumer No", "LPG ID", "Name", "Father Name", "Mobile", "Email", "Address", "Pincode",
           "Category", "Connection Type", "Cylinder Type", "Connection Date", "Remarks"]

@role_required("manager")
def template_download(request):
    wb = Workbook(); ws = wb.active; ws.title = "Consumers"
    ws.append(HEADERS)
    ws.append(["123456", "", "Sample Name", "Sample Father", "9876543210", "", "House name, Kasaragod", "671121",
               "Domestic", "Single", "14.2 kg", "15-06-2020", ""])
    resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = 'attachment; filename="consumers_template.xlsx"'
    wb.save(resp)
    return resp