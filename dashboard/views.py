from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from accounts.utils import role_required
from connection.models import NewConnection
from gas.models import Booking, Enquiry
from shop.models import Order, Product

User = get_user_model()

def _customers():
    return User.objects.exclude(is_superuser=True).exclude(profile__role__in=["staff", "manager"])

# ---------------- helpers ----------------
def _val(v):
    if v is None: return ""
    if isinstance(v, datetime):
        if timezone.is_aware(v): v = timezone.localtime(v).replace(tzinfo=None)
        return v
    if isinstance(v, bool): return "Yes" if v else "No"
    if isinstance(v, Decimal): return float(v)
    if isinstance(v, str): return ILLEGAL_CHARACTERS_RE.sub("", v)
    return v

def _disp(v):
    v = _val(v)
    if isinstance(v, datetime): return v.strftime("%d %b %Y, %I:%M %p")
    if isinstance(v, float): return f"{v:,.2f}"
    return v

def _dates(request):
    def p(k):
        try: return datetime.strptime(request.GET.get(k, ""), "%Y-%m-%d").date()
        except ValueError: return None
    return p("from"), p("to")

def _between(qs, field, d1, d2):
    if d1: qs = qs.filter(**{field + "__date__gte": d1})
    if d2: qs = qs.filter(**{field + "__date__lte": d2})
    return qs

# ---------------- report builders: return headers, rows, status column index, status labels ----------------
def _b_bookings(d1, d2):
    qs = _between(Booking.objects.select_related("cylinder", "customer"), "created", d1, d2)
    headers = ["Booking no", "Date", "Name", "Phone", "Consumer no", "Cylinder", "Qty", "Address", "Status", "Account"]
    rows = [[b.pk, b.created, b.name, b.phone, b.consumer_no, str(b.cylinder), b.quantity, b.address,
             b.get_status_display(), b.customer.username if b.customer else ""] for b in qs]
    return headers, rows, 8, [l for _, l in Booking.STATUS]

GAS = {"new": "Not yet confirmed", "confirmed": "To deliver", "delivered": "Delivered", "cancelled": "Cancelled"}
SHOP = {"placed": "To deliver", "packed": "To deliver", "shipped": "Out for delivery", "delivered": "Delivered", "cancelled": "Cancelled"}

def _b_deliveries(d1, d2):
    rows = []
    for b in _between(Booking.objects.select_related("cylinder"), "created", d1, d2):
        rows.append(["Gas cylinder", f"#{b.pk}", b.created, b.name, b.phone, b.address,
                     f"{b.cylinder} x {b.quantity}", GAS[b.status], ""])
    qs = _between(Order.objects.filter(confirmed=True).prefetch_related("items", "events"), "created", d1, d2)
    for o in qs:
        done = [e.created for e in o.events.all() if e.status == "delivered"]
        rows.append(["Accessories", o.order_no, o.created, o.name, o.phone, o.address,
                     ", ".join(f"{i.name} x {i.qty}" for i in o.items.all()), SHOP.get(o.status, o.status),
                     done[-1] if done else ""])
    rows.sort(key=lambda r: r[2], reverse=True)
    headers = ["Type", "Reference", "Date", "Customer", "Phone", "Address", "Items", "Delivery status", "Delivered on"]
    return headers, rows, 7, ["Not yet confirmed", "To deliver", "Out for delivery", "Delivered", "Cancelled"]

def _b_orders(d1, d2):
    qs = _between(Order.objects.filter(confirmed=True).prefetch_related("items"), "created", d1, d2)
    headers = ["Order no", "Date", "Name", "Phone", "Address", "Items", "Total (INR)", "Payment method", "Payment status", "Order status"]
    rows = [[o.order_no, o.created, o.name, o.phone, o.address,
             ", ".join(f"{i.name} x {i.qty}" for i in o.items.all()), o.total,
             o.get_payment_method_display(), o.get_payment_status_display(), o.get_status_display()] for o in qs]
    return headers, rows, 9, [l for k, l in Order.STATUS if k != "awaiting"]

def _b_connections(d1, d2):
    qs = _between(NewConnection.objects.select_related("cylinder"), "created", d1, d2)
    headers = ["Application no", "Date", "Name", "Father / spouse", "Phone", "Email", "Address", "Pincode",
               "Connection", "Cylinder", "Aadhaar", "Status", "Remarks"]
    rows = [[a.application_no, a.created, a.name, a.father_name, a.phone, a.email, a.address, a.pincode,
             a.get_connection_type_display(), str(a.cylinder), "XXXX XXXX " + a.aadhaar_last4,
             a.get_status_display(), a.remarks] for a in qs]
    return headers, rows, 11, [l for _, l in NewConnection.STATUS]

def _b_customers(d1, d2):
    qs = _between(_customers().annotate(nb=Count("bookings", distinct=True), no=Count("shop_orders", distinct=True)),
                  "date_joined", d1, d2).order_by("-date_joined")
    headers = ["Username", "Full name", "Phone", "Email", "Joined", "Last login", "Active", "Gas bookings", "Accessory orders"]
    rows = [[u.username, u.get_full_name(), getattr(getattr(u, "profile", None), "phone", ""), u.email,
             u.date_joined, u.last_login, u.is_active, u.nb, u.no] for u in qs]
    return headers, rows, None, []

def _b_products(d1, d2):
    headers = ["Product", "Category", "Price (INR)", "Stock", "Active"]
    rows = [[p.name, p.category, p.price, p.stock, p.active] for p in Product.objects.all()]
    return headers, rows, None, []

def _b_enquiries(d1, d2):
    qs = _between(Enquiry.objects.all(), "created", d1, d2)
    headers = ["Date", "Name", "Phone", "Message"]
    return headers, [[e.created, e.name, e.phone, e.message] for e in qs], None, []

REPORTS = {
    "bookings": ("Gas bookings", _b_bookings, "Every cylinder booking with status"),
    "deliveries": ("Deliveries", _b_deliveries, "Gas and accessory deliveries: to deliver, out, delivered"),
    "orders": ("Accessory orders", _b_orders, "Shop orders with payment and order status"),
    "connections": ("New connections", _b_connections, "Applications with verification status"),
    "customers": ("Customers", _b_customers, "Customer data with booking and order counts"),
    "products": ("Products and stock", _b_products, "Accessories, prices and stock"),
    "enquiries": ("Enquiries", _b_enquiries, "Messages from the contact form"),
}

def _collect(request, kind):
    if kind not in REPORTS: raise Http404
    title, build, _ = REPORTS[kind]
    d1, d2 = _dates(request)
    headers, rows, si, labels = build(d1, d2)
    st = request.GET.get("status", "")
    if si is not None and st in labels: rows = [r for r in rows if r[si] == st]
    else: st = ""
    q = request.GET.get("q", "").strip()
    if q: rows = [r for r in rows if q.lower() in " ".join(str(_val(c)) for c in r).lower()]
    return {"kind": kind, "title": title, "headers": headers, "rows": rows, "si": si, "labels": labels,
            "d1": d1, "d2": d2, "st": st, "q": q}

# ---------------- Excel ----------------
def _xlsx(filename, sheets):
    wb = Workbook(); wb.remove(wb.active)
    fill = PatternFill("solid", fgColor="0A3B8C")
    for title, headers, rows in sheets:
        ws = wb.create_sheet(title[:31])
        for j, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=j, value=h)
            c.font = Font(bold=True, color="FFFFFF"); c.fill = fill; c.alignment = Alignment(vertical="center")
        widths = [len(h) for h in headers]
        for i, row in enumerate(rows, 2):
            for j, v in enumerate(row, 1):
                v = _val(v); c = ws.cell(row=i, column=j, value=v)
                if isinstance(v, str): c.data_type = "s"        # text only, never a formula
                elif isinstance(v, datetime): c.number_format = "dd-mm-yyyy hh:mm"
                widths[j - 1] = max(widths[j - 1], min(len(str(v)), 50))
        for j, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(j)].width = w + 3
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp

@role_required("manager")
def export(request, kind):
    rep = _collect(request, kind)
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M")
    return _xlsx(f"{kind}_{stamp}.xlsx", [(rep["title"], rep["headers"], rep["rows"])])

@role_required("manager")
def export_all(request):
    d1, d2 = _dates(request)
    sheets = [(t, *b(d1, d2)[:2]) for t, b, _ in REPORTS.values()]
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M")
    return _xlsx(f"all_reports_{stamp}.xlsx", sheets)

# ---------------- Report page ----------------
@role_required("manager")
def report(request, kind):
    rep = _collect(request, kind)
    page = Paginator(rep["rows"], 25).get_page(request.GET.get("page"))
    q = request.GET.copy(); q.pop("page", None)
    ctx = dict(rep, rows=[[_disp(c) for c in r] for r in page], page=page, total=len(rep["rows"]),
               qs=q.urlencode(), si=-1 if rep["si"] is None else rep["si"],
               tabs=[(k, v[0]) for k, v in REPORTS.items()])
    return render(request, "dashboard/report.html", ctx)

# ---------------- Dashboard home ----------------
@role_required("manager")
def home(request):
    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    per = {r["created__date"]: r["n"] for r in
           Booking.objects.filter(created__date__gte=days[0]).values("created__date").annotate(n=Count("id"))}
    top = max([per.get(d, 0) for d in days] + [1])
    bars = [{"label": d.strftime("%a"), "n": per.get(d, 0), "pct": int(per.get(d, 0) * 100 / top)} for d in days]

    counts = dict(Booking.objects.values_list("status").annotate(n=Count("id")))
    total = sum(counts.values()) or 1
    status_rows = [(label, counts.get(k, 0), int(counts.get(k, 0) * 100 / total)) for k, label in Booking.STATUS]

    confirmed_orders = Order.objects.filter(confirmed=True)
    sales = confirmed_orders.exclude(status="cancelled").aggregate(t=Sum("total"))["t"] or Decimal("0")
    to_deliver = counts.get("confirmed", 0) + confirmed_orders.filter(status__in=["placed", "packed", "shipped"]).count()
    delivered = counts.get("delivered", 0) + confirmed_orders.filter(status="delivered").count()
    pending_nc = NewConnection.objects.filter(status__in=["submitted", "verifying"]).count()
    low = Product.objects.filter(active=True, stock__lte=5).order_by("stock")
    R = lambda k, extra="": reverse("report", args=[k]) + extra

    cards = [
        {"label": "New bookings", "value": counts.get("new", 0), "note": "waiting for a call", "color": "blue", "url": R("bookings", "?status=New")},
        {"label": "To deliver", "value": to_deliver, "note": "gas and accessories", "color": "orange", "url": R("deliveries", "?status=To+deliver")},
        {"label": "Delivered", "value": delivered, "note": "all time", "color": "green", "url": R("deliveries", "?status=Delivered")},
        {"label": "Customers", "value": _customers().count(), "note": "registered accounts", "color": "navy", "url": R("customers")},
        {"label": "Connection requests", "value": pending_nc, "note": "to verify", "color": "purple", "url": R("connections")},
        {"label": "Accessory sales", "value": f"₹{sales:,.0f}", "note": "excluding cancelled", "color": "red", "url": R("orders")},
        {"label": "Low stock items", "value": low.count(), "note": "5 or fewer left", "color": "orange", "url": R("products")},
        {"label": "Enquiries", "value": Enquiry.objects.count(), "note": "all time", "color": "navy", "url": R("enquiries")},
    ]
    n = {"bookings": Booking.objects.count(), "orders": confirmed_orders.count(), "connections": NewConnection.objects.count(),
         "customers": _customers().count(), "products": Product.objects.count(), "enquiries": Enquiry.objects.count()}
    n["deliveries"] = n["bookings"] + n["orders"]
    hub = [{"kind": k, "title": v[0], "note": v[2], "count": n[k]} for k, v in REPORTS.items()]
    return render(request, "dashboard/home.html", {
        "today": today, "cards": cards, "bars": bars, "status_rows": status_rows, "low": low[:6], "hub": hub,
        "recent_bookings": Booking.objects.select_related("cylinder")[:6],
        "recent_orders": confirmed_orders[:6],
        "recent_connections": NewConnection.objects.select_related("cylinder")[:5],
    })