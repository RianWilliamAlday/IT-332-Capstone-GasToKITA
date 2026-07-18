import os
import requests

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

PUMP_MAP = {
    "Regular 1": 1,
    "Regular 2": 2,
    "Premium 1": 3,
    "Premium 2": 4,
    "Diesel 1": 5,
    "Diesel 2": 6,
}

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}

def get_fuels(auth: dict):
    """Returns list[FuelTypeResponse] from /api/fuels"""
    r = requests.get(f"{BASE_URL}/api/fuels", headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def get_oils(auth: dict):
    """Returns list[OilProduct] from /oils (no /api prefix in your backend)"""
    r = requests.get(f"{BASE_URL}/oils", headers=_headers(auth), timeout=10)
    r.raise_for_status()
    return r.json()

def create_fuel_sale(auth: dict, pump_id: int, liters_sold: float, attendant_name: str, payment_method: str = "cash"):
    """POST /api/sales/fuel"""
    payload = {
        "pump_id": pump_id,
        "liters_sold": liters_sold,
        "attendant_name": attendant_name,
        "payment_method": payment_method,
    }
    r = requests.post(f"{BASE_URL}/api/sales/fuel", json=payload, headers=_headers(auth), timeout=15)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except:
            detail = r.text
        raise Exception(detail or f"Fuel sale failed {r.status_code}")
    return r.json()

def create_oil_sale(auth: dict, oil_id: int, quantity: int, attendant_name: str, payment_method: str = "cash"):
    """POST /api/sales/oil"""
    payload = {
        "oil_id": oil_id,
        "quantity": quantity,
        "payment_method": payment_method,
        "attendant_name": attendant_name,
    }
    r = requests.post(f"{BASE_URL}/api/sales/oil", json=payload, headers=_headers(auth), timeout=15)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except:
            detail = r.text
        raise Exception(detail or f"Oil sale failed {r.status_code}")
    return r.json()
