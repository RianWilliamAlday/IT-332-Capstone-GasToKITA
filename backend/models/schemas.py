from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, date

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
    threshold: float
    needs_restock: bool

class RestockRequest(BaseModel):
    liters_added: float
    cost: float
    supplier: Optional[str] = None

class ThresholdUpdate(BaseModel):
    threshold: float

class SaleCreate(BaseModel):
    pump_id: int
    liters_sold: float
    attendant_name: str
    payment_method: str = "cash"

class SaleResponse(BaseModel):
    id: int
    fuel_name: str
    pump_name: str
    attendant_name: str
    recorded_by: str
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
    by_fuel: dict

class SaleHistoryItem(BaseModel):
    id: int
    sold_at: datetime
    fuel_id: int
    pump_id: int
    attendant_name: str
    liters_sold: float
    price_per_liter: float
    total_amount: float
    payment_method: str
    recorded_by: str

class SalesHistoryResponse(BaseModel):
    sales: List[SaleHistoryItem]
    total_count: int
    total_amount: float
    total_liters: float
    page: int
    page_size: int

class SalesFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    fuel_id: Optional[int] = None
    attendant_name: Optional[str] = None
    pump_id: Optional[int] = None
    payment_method: Optional[str] = None
    page: int = 1
    page_size: int = 50

class InventoryMetrics(BaseModel):
    fuel_id: int
    fuel_name: str
    current_stock: float
    tank_capacity: float
    threshold: float
    avg_daily_usage: float
    usage_std_dev: float
    max_daily_usage: float
    trend: Literal["increasing", "decreasing", "stable"]
    days_remaining: float
    safety_stock: float
    reorder_point: float
    economic_order_qty: float
    max_stock_level: float
    should_reorder: bool
    suggested_reorder_date: date
    suggested_quantity: float
    urgency: Literal["critical", "warning", "normal", "overstocked"]
    message: str
    cost_of_order: float
    days_of_supply_after_reorder: float

class AIInventoryMetrics(InventoryMetrics):
    ai_urgency_explanation: str
    ai_demand_insight: str
    ai_purchase_recommendation: str
    ai_risk_factors: List[str]
    ai_action_items: List[str]