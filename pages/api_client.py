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