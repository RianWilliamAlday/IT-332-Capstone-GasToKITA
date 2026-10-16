import os, requests, pathlib

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

PUMP_MAP = {"Regular 1":1,"Regular 2":2,"Premium 1":3,"Premium 2":4,"Diesel 1":5,"Diesel 2":6}
DEFAULT_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_attendants(auth: dict):
    r = requests.get(f"{BASE_URL}/api/attendants", headers=_headers(auth), timeout=5)
    if r.status_code == 404:
        r = requests.get(f"{BASE_URL}/attendants", headers=_headers(auth), timeout=5)
    r.raise_for_status()
    return r.json()

def get_attendant_names(auth: dict):
    try:
        data = get_attendants(auth)
        if isinstance(data, list):
            names = []
            for item in data:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("full_name") or item.get("username")
                    if name:
                        names.append(name)
            return names if names else DEFAULT_ATTENDANTS
    except Exception as e:
        print(f"[API] get_attendants failed, using defaults: {e}")
    return DEFAULT_ATTENDANTS

def get_fuels(auth: dict):
    r = requests.get(f"{BASE_URL}/api/fuels", headers=_headers(auth), timeout=5)
    r.raise_for_status()
    return r.json()

def get_oils(auth: dict):
    r = requests.get(f"{BASE_URL}/oils", headers=_headers(auth), timeout=5)
    if r.status_code == 404:
        r = requests.get(f"{BASE_URL}/api/oils", headers=_headers(auth), timeout=5)
    r.raise_for_status()
    return r.json()

def create_fuel_sale(auth: dict, pump_id: int, liters_sold: float, attendant_name: str, payment_method: str = "cash", amount_paid: float = 0):
    payload = {"pump_id": pump_id, "liters_sold": liters_sold, "attendant_name": attendant_name, "payment_method": payment_method, "amount_paid": amount_paid}
    r = requests.post(f"{BASE_URL}/api/sales/fuel", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Fuel sale failed {r.status_code}")
    return r.json()

def create_oil_sale(auth: dict, oil_id: int, quantity: int, attendant_name: str, payment_method: str = "cash", amount_paid: float = 0):
    payload = {"oil_id": oil_id, "quantity": quantity, "payment_method": payment_method, "attendant_name": attendant_name, "amount_paid": amount_paid}
    r = requests.post(f"{BASE_URL}/api/sales/oil", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Oil sale failed {r.status_code}")
    return r.json()

def save_receipt_pdf(auth: dict, sale_id: int, receipt_no: str, product_type="fuel", save_dir=None):
    headers = _headers(auth)
    r = requests.get(f"{BASE_URL}/api/receipts/{product_type}/{sale_id}/pdf", headers=headers, timeout=15)
    r.raise_for_status()
    if save_dir is None:
        save_dir = pathlib.Path.home() / "Downloads"
    file_path = pathlib.Path(save_dir) / f"receipt_{receipt_no}.pdf"
    file_path.write_bytes(r.content)
    return str(file_path)

def submit_multi_sale(auth: dict, *args, **kwargs):
    data = {}
    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            data.update(a)
        elif isinstance(a, (list, tuple)):
            first = a[0] if a else {}
            if isinstance(first, dict) and "pump_id" in first:
                data["fuel_items"] = list(a)
            elif isinstance(first, dict) and ("oil_id" in first or "oil_product_id" in first):
                data["oil_items"] = list(a)
            elif not a:
                pass
            else:
                raise TypeError(f"submit_multi_sale: can't tell what this list is: {a!r}")
        elif isinstance(a, str):
            if a.strip().lower() in ("cash", "gcash"):
                data["payment_method"] = a.strip().lower()
            else:
                data["attendant_name"] = a
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            data["amount_paid"] = float(a)
        else:
            raise TypeError(f"submit_multi_sale: unexpected argument {a!r}")
    data.update(kwargs)

    cart = auth.get("cart", {})
    if "fuel_items" not in data or not data["fuel_items"]:
        data["fuel_items"] = cart.get("fuel_items", [])
    if "oil_items" not in data or not data["oil_items"]:
        data["oil_items"] = cart.get("oil_items", [])

    if "attendant_name" not in data or not data["attendant_name"]:
        attendant = auth.get("selected_attendant") or auth.get("name") or auth.get("user") or "Attendant 1"
        if isinstance(attendant, dict):
            attendant = attendant.get("name", "Attendant 1")
        data["attendant_name"] = attendant

    data.setdefault("payment_method", "cash")
    data.setdefault("amount_paid", 0)

    fixed = []
    for o in data["oil_items"]:
        o = dict(o)
        if "oil_id" not in o and "oil_product_id" in o:
            o["oil_id"] = o["oil_product_id"]
        fixed.append(o)
    data["oil_items"] = fixed

    r = requests.post(f"{BASE_URL}/api/sales/multi", json=data, headers=_headers(auth), timeout=15)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Multi sale failed {r.status_code}")
    return r.json()

create_multi_sale = submit_multi_sale

def create_gcash_dialog_checkout(auth: dict, product_type: str = "fuel", attendant_name: str = "", pump_id: int = None, fuel_id: int = None, liters_sold: float = None, oil_product_id: int = None, quantity: int = None, fuel_items: list = None, oil_items: list = None):
    """
    Called when user clicks GCash button INSIDE liters/qty dialog (or the multi-cart checkout)
    POST /api/payments/gcash/dialog-checkout
    product_type: "fuel" | "oil" | "multi"
    For "multi": fuel_items=[{"pump_id", "liters_sold"}], oil_items=[{"oil_product_id", "quantity"}]
    Returns: {sale_id, checkout_id, checkout_url, total_amount, status}
    """
    payload = {
        "product_type": product_type,
        "attendant_name": attendant_name
    }
    if product_type == "multi":
        payload["fuel_items"] = fuel_items or []
        payload["oil_items"] = oil_items or []
    elif product_type == "fuel":
        if pump_id is not None: payload["pump_id"] = pump_id
        if fuel_id is not None: payload["fuel_id"] = fuel_id
        if liters_sold is not None: payload["liters_sold"] = float(liters_sold)
    else:
        if oil_product_id is not None: payload["oil_product_id"] = int(oil_product_id)
        if quantity is not None: payload["quantity"] = int(quantity)

    r = requests.post(f"{BASE_URL}/api/payments/gcash/dialog-checkout", json=payload, headers=_headers(auth), timeout=15)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"GCash checkout failed {r.status_code}: {r.text}")
    return r.json()

def check_gcash_status(auth: dict, checkout_id: str):
    """
    Poll this after showing QR. Frontend polls every 3s
    GET /api/payments/gcash/status/{checkout_id}
    Returns: {is_paid: bool, sale_id, payment_status}
    """
    r = requests.get(f"{BASE_URL}/api/payments/gcash/status/{checkout_id}", headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"GCash status check failed {r.status_code}")
    return r.json()

def manual_confirm_gcash(auth: dict, sale_id: int, product_type: str = "fuel", gcash_ref: str = None):
    """
    Fallback for defense / when ngrok webhook fails. Marks pending sale as paid and deducts FIFO
    POST /api/payments/gcash/manual-confirm/{sale_id}?product_type=fuel&gcash_ref=xxx
    """
    params = {"product_type": product_type}
    if gcash_ref: params["gcash_ref"] = gcash_ref
    r = requests.post(f"{BASE_URL}/api/payments/gcash/manual-confirm/{sale_id}", params=params, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Manual confirm failed {r.status_code}")
    return r.json()