import os, requests, pathlib

BASE_URL = os.getenv("API_URL", "http://192.168.1.100:8000")

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