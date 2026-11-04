import csv
import io
from datetime import date, datetime
from django.db import transaction
from openpyxl import load_workbook
from .models import Consumer

MAX_ROWS = 20000

def norm(s):
    return " ".join(str(s or "").replace("_", " ").replace("-", " ").replace("/", " ").lower().split())

ALIASES = {
    "consumer_no": ["consumer no", "consumer number", "consumerno", "consumer id", "consumer"],
    "name": ["name", "consumer name", "customer name"],
    "father_name": ["father name", "father husband name", "father or husband name", "husband name",
                    "spouse name", "guardian name", "father spouse name"],
    "lpg_id": ["lpg id", "lpgid", "lpg no"],
    "phone": ["mobile", "mobile no", "mobile number", "phone", "phone number", "contact", "contact no"],
    "email": ["email", "email id", "e mail"],
    "pincode": ["pincode", "pin code", "pin"],
    "category": ["category", "consumer category", "consumer type", "type"],
    "connection_type": ["connection type", "type of connection", "scheme"],
    "cylinder_type": ["cylinder type", "cylinder", "cylinder size", "cylinders"],
    "connection_date": ["connection date", "date of connection", "connected on", "date"],
    "remarks": ["remarks", "remark", "notes", "note"],
}
ADDRESS = ["address", "address 1", "address1", "address 2", "address2", "address 3", "address3",
           "village", "area", "locality", "city", "town"]
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y", "%d-%b-%Y", "%d %b %Y")

def _read_rows(f, filename):
    if filename.lower().endswith(".csv"):
        raw = f.read()
        try: text = raw.decode("utf-8-sig")
        except UnicodeDecodeError: text = raw.decode("cp1252")
        return list(csv.reader(io.StringIO(text)))
    ws = load_workbook(f, read_only=True, data_only=True).active
    return [list(r) for r in ws.iter_rows(values_only=True)]

def _raw(row, i):
    return row[i] if i is not None and i < len(row) else None

def _cell(row, i):
    v = _raw(row, i)
    if v is None: return ""
    if isinstance(v, float) and v.is_integer(): v = int(v)
    return str(v).strip()

def _digits(s, n=None):
    d = "".join(c for c in str(s) if c.isdigit())
    return d[-n:] if n else d

def _date(v):
    if isinstance(v, datetime): return v.date()
    if isinstance(v, date): return v
    s = str(v or "").strip()
    if not s: return None
    for cand in (s, s.split()[0]):
        for fmt in DATE_FORMATS:
            try: return datetime.strptime(cand, fmt).date()
            except ValueError: pass
    return None

def import_file(f, filename, dry=False):
    rows = [r for r in _read_rows(f, filename) if any(c not in (None, "") for c in r)]
    if len(rows) < 2: raise ValueError("The file has no data rows.")
    if len(rows) > MAX_ROWS + 1: raise ValueError(f"Too many rows. Upload at most {MAX_ROWS} at a time.")
    head = [norm(c) for c in rows[0]]

    idx = {}
    for key, names in ALIASES.items():
        wanted = [norm(n) for n in names]
        for i, h in enumerate(head):
            if h in wanted and i not in idx.values():
                idx[key] = i; break
    addr_cols = [i for i, h in enumerate(head) if h in [norm(a) for a in ADDRESS]]
    if "consumer_no" not in idx or "name" not in idx:
        raise ValueError("Could not find the 'Consumer No' and 'Name' columns. Columns found: "
                         + ", ".join(str(c) for c in rows[0] if c))

    ignored = [i for i, h in enumerate(head) if any(w in h for w in ("aadhaar", "aadhar", "uid"))]
    used = set(idx.values()) | set(addr_cols) | set(ignored)
    unknown = [str(rows[0][i]) for i in range(len(head)) if i not in used and head[i]]
    mapped = [f"{rows[0][i]} = {k.replace('_', ' ')}" for k, i in idx.items()]
    if addr_cols: mapped.append(", ".join(str(rows[0][i]) for i in addr_cols) + " = address")

    created = updated = skipped = 0
    errors = []
    with transaction.atomic():
        for n, row in enumerate(rows[1:], 2):
            no, name = _cell(row, idx["consumer_no"]), _cell(row, idx["name"])
            if not no or not name:
                skipped += 1
                if len(errors) < 10: errors.append(f"Row {n}: consumer number or name is empty.")
                continue
            email = _cell(row, idx.get("email"))
            data = {
                "name": name[:120],
                "father_name": _cell(row, idx.get("father_name"))[:120],
                "lpg_id": _cell(row, idx.get("lpg_id"))[:30],
                "phone": _digits(_cell(row, idx.get("phone")), 10),
                "email": email[:254] if "@" in email else "",
                "address": ", ".join(p for p in (_cell(row, i) for i in addr_cols) if p),
                "pincode": _digits(_cell(row, idx.get("pincode")))[:6],
                "category": _cell(row, idx.get("category"))[:60],
                "connection_type": _cell(row, idx.get("connection_type"))[:60],
                "cylinder_type": _cell(row, idx.get("cylinder_type"))[:60],
                "connection_date": _date(_raw(row, idx.get("connection_date"))),
                "remarks": _cell(row, idx.get("remarks"))[:250],
            }
            # empty cells never erase data that is already saved
            data = {k: v for k, v in data.items() if v not in ("", None)}
            _, was_new = Consumer.objects.update_or_create(consumer_no=no[:30], defaults=data)
            if was_new: created += 1
            else: updated += 1
        if dry: transaction.set_rollback(True)
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors,
            "unknown": unknown, "mapped": mapped, "dry": dry}