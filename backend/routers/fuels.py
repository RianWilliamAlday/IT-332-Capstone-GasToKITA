from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.database import get_session, Fuel
from models.schemas import FuelTypeResponse, PriceUpdate
from services.dipstick import get_closest_dipstick_reading

router = APIRouter(prefix="/api/fuels", tags=["fuels"])

@router.get("", response_model=list[FuelTypeResponse])
def get_fuels(session: Session = Depends(get_session)):
    fuels = session.exec(select(Fuel)).all()
    response_data = []
    for fuel in fuels:
        cm, display_liters = get_closest_dipstick_reading(fuel.actual_liters)
        # Use the fuel's own capacity and cap at 100%
        percentage = min(100.0, round((display_liters / fuel.tank_capacity) * 100, 2))
        response_data.append(FuelTypeResponse(
            id=fuel.id,
            name=fuel.name,
            price=fuel.price,
            actual_liters=fuel.actual_liters,
            tank_capacity=fuel.tank_capacity, # <-- include this
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