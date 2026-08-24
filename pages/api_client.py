import os, requests, pathlib

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
DEFAULT_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]
PUMP_MAP = {"Regular 1":1,"Regular 2":2,"Premium 1":3,"Premium 2":4,"Diesel 1":5,"Diesel 2":6}

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

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

def restock_fuel(auth: dict, fuel_id: int, liters_added: float, cost: float = 0, supplier: str = "Admin", selling_price: float = 0):
    payload = {"liters_added": liters_added, "cost": cost, "selling_price": float(selling_price)}
    if supplier and isinstance(supplier, str) and supplier.strip():
        payload["supplier"] = supplier.strip()
    r = requests.post(f"{BASE_URL}/api/fuels/{fuel_id}/restock", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def update_fuel_price(auth: dict, fuel_id: int, new_price: float):
    r = requests.patch(f"{BASE_URL}/api/fuels/{fuel_id}/price", json={"price": new_price}, headers=_headers(auth), timeout=8)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def update_fuel_threshold(auth: dict, fuel_id: int, new_threshold: float):
    r = requests.patch(f"{BASE_URL}/api/fuels/{fuel_id}/threshold", json={"threshold": new_threshold}, headers=_headers(auth), timeout=8)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def dipstick_convert(auth: dict, cm: int, fuel_name: str):
    r = requests.get(f"{BASE_URL}/api/fuels/dipstick", params={"cm": cm, "fuel_name": fuel_name}, headers=_headers(auth), timeout=5)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def sync_dipstick(auth: dict, fuel_id: int, cm: int):
    r = requests.post(f"{BASE_URL}/api/fuels/{fuel_id}/sync-dipstick?cm={cm}", headers=_headers(auth), timeout=8)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def create_oil_product(auth: dict, brand: str, name: str, stock: int, price: float, variant: str = "", low_threshold: int = 5):
    payload = {"brand": brand, "name": name, "variant": variant or None, "stock": stock, "price": price, "cost": cost, "low_stock_threshold": low_threshold}
    r = requests.post(f"{BASE_URL}/oils/", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def restock_oil(auth: dict, oil_id: int, quantity: int, total_cost: float, supplier: str = "Admin"):
    payload = {"quantity_added": quantity, "total_cost": total_cost, "supplier": supplier}
    r = requests.post(f"{BASE_URL}/oils/{oil_id}/restock", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()

def get_peak_hours(auth: dict, days: int = 30, product_type: str = "all", fuel_id=None, oil_id=None):
    params = {"days": days, "product_type": product_type}
    if fuel_id: params["fuel_id"] = fuel_id
    if oil_id: params["oil_id"] = oil_id
    r = requests.get(f"{BASE_URL}/analytics/peak-hours", params=params, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_heatmap(auth: dict, days: int = 30, product_type: str = "fuel"):
    r = requests.get(f"{BASE_URL}/analytics/heatmap", params={"days": days, "product_type": product_type}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_fuel_profit_margins(auth: dict, days: int = 30):
    r = requests.get(f"{BASE_URL}/analytics/profit-margins/fuel", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_oil_profit_margins(auth: dict, days: int = 30):
    r = requests.get(f"{BASE_URL}/analytics/profit-margins/oil", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_unified_profit_margins(auth: dict, days: int = 30):
    r = requests.get(f"{BASE_URL}/analytics/profit-margins/unified", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_revenue_summary(auth: dict, days: int = 30):
    r = requests.get(f"{BASE_URL}/analytics/revenue/summary", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_top_oils(auth: dict, days: int = 30, limit: int = 5):
    r = requests.get(f"{BASE_URL}/analytics/oil/top-selling", params={"days": days, "limit": limit}, headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_unified_history(auth: dict, product_type=None, attendant_name=None, start_date=None, end_date=None, page=1, page_size=100):
    params = {"page": page, "page_size": page_size}
    if product_type and product_type != "all": params["product_type"] = product_type
    if attendant_name and attendant_name != "all": params["attendant_name"] = attendant_name
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    r = requests.get(f"{BASE_URL}/api/sales/history", params=params, headers=_headers(auth), timeout=8)
    r.raise_for_status()
    return r.json()

def update_oil(auth: dict, oil_id: int, payload: dict):
    url = f"{BASE_URL}/oils/{oil_id}" 
    headers = {
        "Authorization": f"Bearer {auth.get('token', '')}",
        "Content-Type": "application/json"
    }
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Server error ({response.status_code}): {response.text}")
    return response.json()

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_attendant_rankings(auth, days=30, product_type="all", sort_by="revenue", limit=10, include_breakdown=False):
    r = requests.get(f"{BASE_URL}/analytics/attendants/ranking", params={
        "days": days, "product_type": product_type, "sort_by": sort_by, "limit": limit, "include_breakdown": include_breakdown
    }, headers=_headers(auth), timeout=10)
    r.raise_for_status(); return r.json()

def get_attendant_leaderboard(auth, days=7):
    r = requests.get(f"{BASE_URL}/analytics/attendants/leaderboard", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status(); return r.json()

def get_attendant_performance(auth, attendant_name, days=30):
    r = requests.get(f"{BASE_URL}/analytics/attendants/{attendant_name}/performance", params={"days": days}, headers=_headers(auth), timeout=10)
    r.raise_for_status(); return r.json()

def download_receipt_pdf(auth: dict, sale_id: int, product_type="fuel"):
    try:
        r = requests.get(
            f"{BASE_URL}/api/receipts/{product_type}/{sale_id}/pdf", 
            headers=_headers(auth), 
            timeout=15
        )
        r.raise_for_status()
        return r.content
    except Exception as ex:
        raise Exception(f"Receipt PDF failed: {ex}")

def save_receipt_pdf(auth: dict, sale_id: int, receipt_no: str, product_type="fuel", save_dir=None):
    pdf_bytes = download_receipt_pdf(auth, sale_id, product_type)
    
    if save_dir is None:
        save_dir = pathlib.Path.home() / "Downloads"
    
    file_path = pathlib.Path(save_dir) / f"receipt_{receipt_no}.pdf"
    file_path.write_bytes(pdf_bytes)
    return str(file_path)

def update_fuel_threshold(auth, fuel_id: int, threshold: float):
    headers = {"Authorization": f"Bearer {auth.get('token')}"}
    resp = requests.patch(
        f"{BASE_URL}/api/fuels/{fuel_id}/threshold", 
        json={"threshold": threshold}, 
        headers=headers
    )
    resp.raise_for_status()
    return resp.json()

def get_active_attendants(auth: dict):
    """
    GET /api/attendants/active
    Returns: [{"id": 1, "name": "Juan", "employee_id": "...", "is_active": True}, ...]
    """
    try:
        r = requests.get(f"{BASE_URL}/api/employees/attendants/active", headers=_headers(auth), timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"[API] /active -> {len(data)} attendants")
            return data
    except Exception as e:
        print(f"[API ERROR] get_active_attendants: {e}")
    return []


def get_attendant_names(auth: dict) -> list[str]:
    """
    GET /api/attendants/names
    Returns: ["Juan", "Pedro", ...]
    This is what your card UI uses - amount of cards = len(this list)
    """
    try:
        r = requests.get(f"{BASE_URL}/api/employees/attendants/names", headers=_headers(auth), timeout=5)
        if r.status_code == 200:
            names = r.json()
            print(f"[API] /names -> {names}")
            return names if names else DEFAULT_ATTENDANTS
    except Exception as e:
        print(f"[API ERROR] get_attendant_names: {e}")
    active = get_active_attendants(auth)
    if active and isinstance(active[0], dict):
        return [a.get("name") or a.get("display_name") for a in active]

    return DEFAULT_ATTENDANTS

def create_gcash_dialog_checkout(auth: dict, product_type: str = "fuel", attendant_name: str = "", pump_id: int = None, fuel_id: int = None, liters_sold: float = None, oil_product_id: int = None, quantity: int = None):
    """
    Called when user clicks GCash button INSIDE liters/qty dialog
    This is the endpoint that creates pending sale + PayMongo checkout_url for QR
    POST /api/payments/gcash/dialog-checkout
    Returns: {sale_id, checkout_id, checkout_url, total_amount, status}
    """
    payload = {
        "product_type": product_type,
        "attendant_name": attendant_name
    }
    if product_type == "fuel":
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

def create_gcash_checkout_legacy(auth: dict, amount: float, description: str = "GASTOKITA GCash"):
    """
    Simple amount-only checkout (if you just want to test PayMongo without creating sale)
    """
    payload = {"amount": amount, "description": description}
    r = requests.post(f"{BASE_URL}/api/payments/gcash/create-checkout", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail)
    return r.json()