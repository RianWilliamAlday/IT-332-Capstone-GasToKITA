from pydantic import BaseModel

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