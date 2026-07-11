from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db.database import get_session, Fuel, RestockLog, Sale
from ..models.schemas import FuelTypeResponse, PriceUpdate, RestockRequest, ThresholdUpdate, InventoryMetrics
from ..services.dipstick import get_closest_dipstick_reading
from ..services.ai_feature import get_ai_reorder_insights
from ..db.data import DIPSTICK_DATA
from statistics import mean, stdev
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import List

router = APIRouter(prefix="/api/fuels", tags=["fuels"])

MAX_CM = max(DIPSTICK_DATA.keys())

def check_low_stock(fuel: Fuel) -> bool:
    return fuel.actual_liters <= fuel.threshold

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
            display_percentage=percentage,
            threshold=fuel.threshold,
            needs_restock=check_low_stock(fuel)
        ))
    return response_data

@router.get("/low-stock", response_model=list[FuelTypeResponse])
def get_low_stock_fuels(session: Session = Depends(get_session)):
    fuels = session.exec(select(Fuel)).all()
    low_stock = []
    for fuel in fuels:
        if check_low_stock(fuel):
            cm, display_liters = get_closest_dipstick_reading(fuel.actual_liters)
            percentage = min(100.0, round((display_liters / fuel.tank_capacity) * 100, 2))
            low_stock.append(FuelTypeResponse(
                id=fuel.id,
                name=fuel.name,
                price=fuel.price,
                actual_liters=fuel.actual_liters,
                tank_capacity=fuel.tank_capacity,
                display_cm=cm,
                display_liters=display_liters,
                display_percentage=percentage,
                threshold=fuel.threshold,
                needs_restock=True
            ))
    return low_stock

@router.post("/{fuel_id}/restock")
def restock_fuel(
    fuel_id: int, 
    data: RestockRequest, 
    session: Session = Depends(get_session)
):
    fuel = session.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")
    
    if data.liters_added <= 0:
        raise HTTPException(400, "Liters added must be positive")
    
    if fuel.actual_liters + data.liters_added > fuel.tank_capacity:
        remaining = fuel.tank_capacity - fuel.actual_liters
        raise HTTPException(
            400, 
            f"Exceeds tank capacity. Only {remaining:.2f}L space left"
        )

    fuel.actual_liters += data.liters_added
    fuel.last_restocked = datetime.now()
    session.add(fuel)

    log = RestockLog(
        fuel_id=fuel.id,
        liters_added=data.liters_added,
        cost=data.cost,
        supplier=data.supplier,
        restocked_by="admin"
    )
    session.add(log)
    session.commit()
    session.refresh(fuel)
    
    cm, display_liters = get_closest_dipstick_reading(fuel.actual_liters)
    
    return {
        "message": f"Restocked {data.liters_added}L of {fuel.name}",
        "fuel_id": fuel.id,
        "new_actual_liters": fuel.actual_liters,
        "new_display_cm": cm,
        "new_display_liters": display_liters,
        "needs_restock": check_low_stock(fuel)
    }

@router.patch("/{fuel_id}/threshold")
def update_threshold(
    fuel_id: int, 
    data: ThresholdUpdate, 
    session: Session = Depends(get_session)
):
    fuel = session.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")
    if data.threshold < 0:
        raise HTTPException(400, "Threshold cannot be negative")
    
    fuel.threshold = data.threshold
    session.add(fuel)
    session.commit()
    
    return {
        "message": "Threshold updated",
        "fuel": fuel.name,
        "new_threshold": fuel.threshold,
        "needs_restock": check_low_stock(fuel)
    }

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

@router.post("/{fuel_id}/sync-dipstick")
def sync_from_dipstick(
    fuel_id: int,
    cm: int = Query(..., ge=0),
    session: Session = Depends(get_session)
):
    fuel = session.get(Fuel, fuel_id)
    if cm not in DIPSTICK_DATA:
        raise HTTPException(400, "Invalid dipstick reading")
    
    new_liters = DIPSTICK_DATA[cm]
    old_liters = fuel.actual_liters
    fuel.actual_liters = new_liters
    fuel.last_restocked = datetime.now()
    session.add(fuel)
    session.commit()
    
    return {
        "message": f"Synced {fuel.name} from dipstick",
        "old_liters": old_liters,
        "new_liters": new_liters,
        "difference": new_liters - old_liters
    }

def get_inventory_optimization(session: Session) -> List[InventoryMetrics]:
    LEAD_TIME_DAYS = 3
    Z_SCORE = 1.65
    ORDERING_COST = 1500.0

    today = date.today()
    start_dt = datetime.combine(today - timedelta(days=14), datetime.min.time())

    fuels = session.exec(select(Fuel)).all()
    all_sales = session.exec(
        select(Sale).where(Sale.sold_at >= start_dt)
    ).all()

    results: List[InventoryMetrics] = []

    for fuel in fuels:
        daily = defaultdict(float)
        for s in all_sales:
            if s.fuel_id == fuel.id:
                daily[s.sold_at.date()] += s.liters_sold
        daily_values = []
        for i in range(14):
            d = today - timedelta(days=13 - i)
            daily_values.append(daily.get(d, 0.0))

        avg_daily = round(mean(daily_values), 2) if daily_values else 0.0
        std_dev = round(stdev(daily_values), 2) if len(daily_values) > 1 else 0.0
        max_daily = round(max(daily_values), 2) if daily_values else 0.0

        first_week = mean(daily_values[:7]) if daily_values else 0
        last_week = mean(daily_values[7:]) if daily_values else 0
        if last_week > first_week * 1.1:
            trend = "increasing"
        elif last_week < first_week * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        current_stock = float(fuel.actual_liters)
        days_remaining = round(current_stock / avg_daily, 1) if avg_daily > 0 else 999.0

        safety_stock = round(Z_SCORE * std_dev * (LEAD_TIME_DAYS ** 0.5), 2)
        reorder_point = round(avg_daily * LEAD_TIME_DAYS + safety_stock, 2)

        max_stock_level = round(fuel.tank_capacity * 0.9, 2)
        should_reorder = current_stock <= reorder_point

        suggested_quantity = round(max(0, max_stock_level - current_stock), 2) if should_reorder else 0.0

        annual_demand = avg_daily * 365
        holding_cost = fuel.price * 0.20
        if holding_cost > 0 and annual_demand > 0:
            eoq = (2 * annual_demand * ORDERING_COST / holding_cost) ** 0.5
            economic_order_qty = round(min(eoq, max_stock_level), 2)
        else:
            economic_order_qty = max_stock_level
        if current_stock <= fuel.threshold or days_remaining < 2:
            urgency = "critical"
        elif current_stock <= reorder_point or days_remaining < 5:
            urgency = "warning"
        elif current_stock > fuel.tank_capacity * 0.85:
            urgency = "overstocked"
        else:
            urgency = "normal"

        suggested_reorder_date = today if should_reorder else today + timedelta(days=max(0, int(days_remaining - LEAD_TIME_DAYS)))
        cost_of_order = round(suggested_quantity * fuel.price, 2)
        days_after = round((current_stock + suggested_quantity) / avg_daily, 1) if avg_daily > 0 else 999.0

        message = f"{fuel.name}: {current_stock:.0f}L left, ~{days_remaining} days at {avg_daily}L/day"

        results.append(InventoryMetrics(
            fuel_id=fuel.id,
            fuel_name=fuel.name,
            current_stock=current_stock,
            tank_capacity=fuel.tank_capacity,
            threshold=fuel.threshold,
            avg_daily_usage=avg_daily,
            usage_std_dev=std_dev,
            max_daily_usage=max_daily,
            trend=trend,
            days_remaining=days_remaining,
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            economic_order_qty=economic_order_qty,
            max_stock_level=max_stock_level,
            should_reorder=should_reorder,
            suggested_reorder_date=suggested_reorder_date,
            suggested_quantity=suggested_quantity,
            urgency=urgency,
            message=message,
            cost_of_order=cost_of_order,
            days_of_supply_after_reorder=days_after
        ))

    return results

class AIInventoryMetrics(InventoryMetrics):
    ai_urgency_explanation: str
    ai_demand_insight: str
    ai_purchase_recommendation: str
    ai_risk_factors: List[str]
    ai_action_items: List[str]

@router.get("/ai-inventory-optimization", response_model=List[AIInventoryMetrics])
def get_ai_inventory_optimization(session: Session = Depends(get_session)):
    base_metrics = get_inventory_optimization(session)
    enhanced_results = []
    for metric in base_metrics:
        fuel_dict = metric.model_dump()
        if metric.urgency in ["critical", "warning", "overstocked"]:
            ai_data = get_ai_reorder_insights(fuel_dict)
        else:
            ai_data = {
                "urgency_explanation": "Stock levels normal",
                "demand_insight": f"Usage stable at {metric.avg_daily_usage}L/day",
                "purchase_recommendation": "No action needed",
                "risk_factors": [],
                "action_items": ["Monitor weekly"]
            }

        enhanced_results.append(AIInventoryMetrics(
            **fuel_dict,
            ai_urgency_explanation=ai_data["urgency_explanation"],
            ai_demand_insight=ai_data["demand_insight"],
            ai_purchase_recommendation=ai_data["purchase_recommendation"],
            ai_risk_factors=ai_data["risk_factors"],
            ai_action_items=ai_data["action_items"]
        ))

    return enhanced_results