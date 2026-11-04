from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.utils import role_of, role_required
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem, Product

# ---------- Products ----------
def shop_home(request):
    qs = Product.objects.filter(active=True)
    cat, q = request.GET.get("cat"), request.GET.get("q", "").strip()
    if cat: qs = qs.filter(category=cat)
    if q: qs = qs.filter(name__icontains=q)
    cats = Product.objects.filter(active=True).order_by("category").values_list("category", flat=True).distinct()
    return render(request, "shop/product_list.html", {"products": qs, "cats": cats, "cat": cat, "q": q})

# ---------- Cart ----------
@require_POST
def cart_add(request):
    p = get_object_or_404(Product, pk=request.POST.get("product"), active=True)
    try: qty = max(1, int(request.POST.get("qty", 1)))
    except ValueError: qty = 1
    cart = Cart(request)
    if cart.qty(p.pk) + qty > p.stock:
        messages.error(request, f"Only {p.stock} of {p.name} in stock.")
    else:
        cart.add(p.pk, qty)
        messages.success(request, f"{p.name} added to cart.")
    return redirect("shop_home")

def cart_detail(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"lines": cart.lines(), "total": cart.total()})

@require_POST
def cart_update(request):
    cart = Cart(request)
    for key, val in request.POST.items():
        if key.startswith("qty_"):
            try: cart.set(int(key[4:]), int(val))
            except ValueError: pass
    messages.success(request, "Cart updated.")
    return redirect("cart_detail")

@require_POST
def cart_remove(request):
    Cart(request).remove(request.POST.get("remove", ""))
    return redirect("cart_detail")

# ---------- Payment helpers ----------
def _gateway():
    kid, sec = settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET
    if not (kid and sec): return None
    import razorpay
    return razorpay.Client(auth=(kid, sec))

def _start_payment(request, order):
    client = _gateway()
    if client is None:
        messages.error(request, "Online payment is not available. Please choose cash on delivery.")
        return redirect("order_detail", order.order_no)
    if not order.gateway_order_id:
        try:
            rz = client.order.create({"amount": int(order.total * 100), "currency": "INR", "receipt": order.order_no})
        except Exception:
            messages.error(request, "Could not start the payment. Please try again.")
            return redirect("order_detail", order.order_no)
        order.gateway_order_id = rz["id"]
        order.save(update_fields=["gateway_order_id"])
    return redirect("pay_page", order.order_no)

@login_required
def pay_page(request, order_no):
    o = get_object_or_404(Order, order_no=order_no, user=request.user)
    if o.confirmed or o.status != "awaiting" or o.payment_method != "online":
        return redirect("order_detail", o.order_no)
    if not o.gateway_order_id:
        return _start_payment(request, o)
    return render(request, "shop/pay.html", {"order": o, "key": settings.RAZORPAY_KEY_ID, "amount": int(o.total * 100)})

# ---------- Checkout & payment ----------
@login_required
def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        messages.error(request, "Your cart is empty.")
        return redirect("shop_home")
    p = getattr(request.user, "profile", None)
    initial = {"name": request.user.get_full_name() or request.user.username, "phone": p.phone if p else ""}
    form = CheckoutForm(request.POST or None, online=_gateway() is not None, initial=initial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            order = Order.objects.create(user=request.user, name=d["name"], phone=d["phone"], address=d["address"],
                                         total=cart.total(), payment_method=d["payment_method"])
            OrderItem.objects.bulk_create([OrderItem(order=order, product=l["product"], name=l["product"].name,
                                           price=l["product"].price, qty=l["qty"]) for l in lines])
        if order.payment_method == "cod":
            order.confirm("cod")
            cart.clear()
            messages.success(request, f"Order {order.order_no} placed. Pay when it is delivered.")
            return redirect("order_detail", order.order_no)
        return _start_payment(request, order)
    return render(request, "shop/checkout.html", {"form": form, "lines": lines, "total": cart.total()})

@login_required
@require_POST
def order_pay(request, order_no):
    o = get_object_or_404(Order, order_no=order_no, user=request.user, status="awaiting", payment_method="online")
    return _start_payment(request, o)

@login_required
@require_POST
def payment_verify(request):
    oid = request.POST.get("razorpay_order_id", "")
    order = get_object_or_404(Order, gateway_order_id=oid, user=request.user)
    client = _gateway()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": oid,
            "razorpay_payment_id": request.POST.get("razorpay_payment_id", ""),
            "razorpay_signature": request.POST.get("razorpay_signature", ""),
        })
    except Exception:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        messages.error(request, "Payment could not be verified. If money was deducted, contact us with your order number.")
        return redirect("order_detail", order.order_no)
    order.gateway_payment_id = request.POST.get("razorpay_payment_id", "")
    order.confirm("paid")
    Cart(request).clear()
    messages.success(request, f"Payment received. Order {order.order_no} is placed.")
    return redirect("order_detail", order.order_no)

# ---------- Orders & tracking ----------
@login_required
def orders(request):
    return render(request, "shop/orders.html", {"orders": Order.objects.filter(user=request.user)})

@login_required
def order_detail(request, order_no):
    o = get_object_or_404(Order, order_no=order_no)
    if o.user_id != request.user.id and role_of(request.user) not in ("staff", "manager"):
        raise PermissionDenied
    flow = [("placed", "Placed"), ("packed", "Packed"), ("shipped", "Out for delivery"), ("delivered", "Delivered")]
    keys = [k for k, _ in flow]
    cur = keys.index(o.status) if o.status in keys else -1
    steps = [(label, i <= cur) for i, (_, label) in enumerate(flow)]
    return render(request, "shop/order_detail.html", {"o": o, "steps": steps})

@role_required("staff", "manager")
def manage_orders(request):
    if request.method == "POST":
        o = get_object_or_404(Order, pk=request.POST.get("order"), confirmed=True)
        st = request.POST.get("status")
        if st in dict(Order.STATUS) and st != "awaiting":
            if st == "cancelled" and o.status != "cancelled":
                for it in o.items.select_related("product"):
                    it.product.stock += it.qty
                    it.product.save(update_fields=["stock"])
            o.status = st
            if st == "delivered" and o.payment_method == "cod": o.payment_status = "paid"
            o.save()
            o.events.create(status=st, note=request.POST.get("note", "").strip()[:200])
            messages.success(request, f"Order {o.order_no} updated to {o.get_status_display()}.")
        return redirect(request.get_full_path())
    qs = Order.objects.filter(confirmed=True).prefetch_related("items")
    f = request.GET.get("status")
    if f in dict(Order.STATUS): qs = qs.filter(status=f)
    statuses = [s for s in Order.STATUS if s[0] != "awaiting"]
    return render(request, "shop/manage.html", {"orders": qs[:100], "statuses": statuses})