from decimal import Decimal  #its for ddecimal calculations
from .models import Product  # importing product models 

class Cart:                                  #creating class compond
    def __init__(self, request):             #__init__ is creating new cart object 
        self.s = request.session            #self.s stores a reference to the session ,request.session accesses that visitor's session
        self.d = self.s.get("cart", {})
    def _save(self): self.s["cart"] = self.d    #_save., self.s["cart"] = self.d Stores the current cart dictionary in the user's Django session.,
    def qty(self, pid): return self.d.get(str(pid), 0)  #str(pid) converts the product ID to a string., .get() looks up that product ID in the cart dictionary.,0 is returned if the product is not in the cart,return sends the result back to the code that called the method.
    def add(self, pid, n=1): self.d[str(pid)] = self.qty(pid) + n; self._save()  #pid is the product ID.,n=1 means the default quantity to add is one.Gets the current quantity using self.qty(pid), Adds the new quantity n and saves the result in the dictionary.
    def set(self, pid, n):
        if n <= 0: self.d.pop(str(pid), None)
        else: self.d[str(pid)] = n
        self._save()
    def remove(self, pid): self.d.pop(str(pid), None); self._save()
    def clear(self): self.d = {}; self._save()
    def count(self): return sum(self.d.values())
    def lines(self):
        out = []
        for p in Product.objects.filter(pk__in=[int(k) for k in self.d], active=True):
            q = min(self.d[str(p.pk)], p.stock)
            if q > 0: out.append({"product": p, "qty": q, "subtotal": p.price * q})
        return out
    def total(self): return sum((l["subtotal"] for l in self.lines()), Decimal("0"))