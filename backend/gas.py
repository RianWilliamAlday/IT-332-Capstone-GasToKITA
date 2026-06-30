from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Gas Station Mock Backend")
# Enable CORS so your frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Models
class FuelType(BaseModel):
    id: int
    name: str
    price: float
    stock_percentage: int
class Pump(BaseModel):
    id: int
    name: str
    fuel_type_id: int
    status: str # e.g., "Available", "In Use"
# Mock Data in Memory
mock_fuel_types = [
    {"id": 1, "name": "Regular", "price": 55.0, "stock_percentage": 100},
    {"id": 2, "name": "Premium", "price": 60.0, "stock_percentage": 50},
    {"id": 3, "name": "Diesel", "price": 50.0, "stock_percentage": 20},
]
mock_pumps = [
    {"id": 1, "name": "Regular 1", "fuel_type_id": 1, "status": "Available"},
    {"id": 2, "name": "Regular 2", "fuel_type_id": 1, "status": "Available"},
    {"id": 3, "name": "Premium 1", "fuel_type_id": 2, "status": "Available"},
    {"id": 4, "name": "Premium 2", "fuel_type_id": 2, "status": "Available"},
    {"id": 5, "name": "Diesel 1", "fuel_type_id": 3, "status": "Available"},
    {"id": 6, "name": "Diesel 2", "fuel_type_id": 3, "status": "Available"},
]
@app.get("/api/fuels", response_model=List[FuelType])
def get_fuels():
    """Returns the list of fuel types and their current stock levels."""
    return mock_fuel_types
@app.get("/api/pumps", response_model=List[Pump])
def get_pumps():
    """Returns the list of all 6 pumps."""
    return mock_pumps
@app.post("/api/dispense")
def dispense_fuel(pump_id: int, amount_percentage: int):
    """
    Mock endpoint to simulate dispensing fuel from a pump.
    Deducts the specified percentage from the corresponding fuel type's stock.
    """
    # Find pump
    pump = next((p for p in mock_pumps if p["id"] == pump_id), None)
    if not pump:
        raise HTTPException(status_code=404, detail="Pump not found")
    
    # Find fuel
    fuel = next((f for f in mock_fuel_types if f["id"] == pump["fuel_type_id"]), None)
    if not fuel:
        raise HTTPException(status_code=404, detail="Fuel type not found")
    
    # Check stock
    if fuel["stock_percentage"] < amount_percentage:
        raise HTTPException(status_code=400, detail="Not enough fuel in stock")
        
    # Deduct stock
    fuel["stock_percentage"] -= amount_percentage
    
    return {
        "message": f"Dispensed {amount_percentage}% from {pump['name']}",
        "remaining_stock": fuel["stock_percentage"]
    }