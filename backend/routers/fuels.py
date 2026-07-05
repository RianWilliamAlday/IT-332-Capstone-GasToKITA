from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db.database import get_session, Fuel
from ..models.schemas import FuelTypeResponse, PriceUpdate
from ..services.dipstick import get_closest_dipstick_reading
import json, os

router = APIRouter(prefix="/api/fuels", tags=["fuels"])

_json_path = os.path.join(os.path.dirname(__file__), "..", "measurements.json")
with open(_json_path, "r") as f:
    DIPSTICK_DATA = {int(k): int(v) for k, v in json.load(f).items()}

MAX_CM = max(DIPSTICK_DATA.keys())

@router.get("/dipstick")
def cm_to_liters(
    cm: int = Query(..., ge=0, description="Dipstick reading in cm"),
    fuel_name: str = Query(..., description="Fuel type: Regular, Premium, Diesel"),
    session: Session = Depends(get_session)
):
    if cm not in DIPSTICK_DATA:
        if cm > MAX_CM:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid capacity. Max dipstick reading is {MAX_CM}cm. Tank may need recalibration."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dipstick reading {cm}cm. No calibration data for this value."
        )

    liters = DIPSTICK_DATA[cm]

    fuel = session.exec(select(Fuel).where(Fuel.name == fuel_name)).first()
    if not fuel:
        raise HTTPException(404, f"Fuel type '{fuel_name}' not found")

    if liters > fuel.tank_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid capacity. {liters}L exceeds {fuel.name} tank capacity of {fuel.tank_capacity}L"
        )

    percentage = min(100.0, round((liters / fuel.tank_capacity) * 100, 2))

    return {
        "input_cm": cm,
        "fuel_type": fuel.name,
        "liters": liters,
        "tank_capacity": fuel.tank_capacity,
        "percentage": percentage
    }

@router.get("", response_model=list[FuelTypeResponse])
def get_fuels(session: Session = Depends(get_session)):
    fuels = session.exec(select(Fuel)).all()
    response_data = []
    for fuel in fuels:
        cm, display_liters = get_closest_dipstick_reading(fuel.actual_liters)
        percentage = min(100.0, round((display_liters / fuel.tank_capacity) * 100, 2))
        response_data.append(FuelTypeResponse(
            id=fuel.id,
            name=fuel.name,
            price=fuel.price,
            actual_liters=fuel.actual_liters,
            tank_capacity=fuel.tank_capacity,
            display_cm=cm,
            display_liters=display_liters,
            display_percentage=percentage
        ))
    return response_data

@router.patch("/{fuel_id}/price")
def update_price(fuel_id: int, data: PriceUpdate, session: Session = Depends(get_session)):
    fuel = session.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")
    if data.price <= 0:
        raise HTTPException(400, "Price must be positive")

    fuel.price = data.price
    session.add(fuel)
    session.commit()
    session.refresh(fuel)
    return {"id": fuel.id, "new_price": fuel.price}