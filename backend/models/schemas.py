from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FuelTypeResponse(BaseModel):
    id: int
    name: str
    price: float
    actual_liters: float
    tank_capacity: float
    display_cm: int
    display_liters: int
    display_percentage: float

class Pump(BaseModel):
    id: int
    name: str
    fuel_type_id: int
    status: str

class DispenseRequest(BaseModel):
    pump_id: int
    amount_liters: float

class PriceUpdate(BaseModel):
    price: float

class FuelTypeResponse(BaseModel):
    id: int
    name: str
    price: float
    actual_liters: float
    tank_capacity: float
    display_cm: int
    display_liters: int
    display_percentage: float
    threshold: float # add
    needs_restock: bool # add

class RestockRequest(BaseModel):
    liters_added: float
    cost: float
    supplier: Optional[str] = None

class ThresholdUpdate(BaseModel):
    threshold: float

class SaleCreate(BaseModel):
    fuel_id: int
    pump_id: int
    liters_sold: float
    attendant_name: str # "Attendant 1", "Attendant 2", "Attendant 3"
    payment_method: str = "cash"
    # recorded_by will come from JWT/token later, hardcode for now

class SaleResponse(BaseModel):
    id: int
    fuel_name: str
    pump_name: str
    attendant_name: str
    recorded_by: str # cashier username
    liters_sold: float
    price_per_liter: float
    total_amount: float
    payment_method: str
    sold_at: datetime

class AttendantSalesSummary(BaseModel):
    attendant_name: str
    total_sales: float
    total_liters: float
    transaction_count: int
    by_fuel: dict # {"Diesel": 5000.0, "Premium": 2300.0}