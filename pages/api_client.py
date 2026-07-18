import os, requests

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

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

def create_fuel_sale(auth: dict, pump_id: int, liters_sold: float, attendant_name: str, payment_method: str = "cash"):
    payload = {"pump_id": pump_id, "liters_sold": liters_sold, "attendant_name": attendant_name, "payment_method": payment_method}
    r = requests.post(f"{BASE_URL}/api/sales/fuel", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Fuel sale failed {r.status_code}")
    return r.json()

def create_oil_sale(auth: dict, oil_id: int, quantity: int, attendant_name: str, payment_method: str = "cash"):
    payload = {"oil_id": oil_id, "quantity": quantity, "payment_method": payment_method, "attendant_name": attendant_name}
    r = requests.post(f"{BASE_URL}/api/sales/oil", json=payload, headers=_headers(auth), timeout=10)
    if r.status_code >= 400:
        try: detail = r.json().get("detail")
        except: detail = r.text
        raise Exception(detail or f"Oil sale failed {r.status_code}")
    return r.json()

def restock_fuel(auth: dict, fuel_id: int, liters_added: float, cost: float = 0, supplier: str = "Admin"):
    payload = {"liters_added": liters_added, "cost": cost, "supplier": supplier}
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
    payload = {"brand": brand, "name": name, "variant": variant or None, "stock": stock, "price": price, "cost": 0, "low_stock_threshold": low_threshold}
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