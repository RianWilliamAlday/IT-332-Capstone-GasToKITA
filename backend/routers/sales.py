from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from..db.database import get_session, Sale, Fuel, User, Pump
from..models.schemas import SaleCreate, SaleResponse, AttendantSalesSummary
from datetime import datetime, date
from typing import List, Optional

router = APIRouter(prefix="/api/sales", tags=["sales"])

VALID_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]

@router.post("/", response_model=SaleResponse)
def create_sale(data: SaleCreate, session: Session = Depends(get_session)):
    if data.attendant_name not in VALID_ATTENDANTS:
        raise HTTPException(400, f"Invalid attendant. Must be one of {VALID_ATTENDANTS}")
    
    fuel = session.get(Fuel, data.fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")
    
    if fuel.actual_liters < data.liters_sold:
        raise HTTPException(400, f"Not enough stock. Only {fuel.actual_liters}L left")
    
    pump = session.get(Pump, data.pump_id)
    if not pump:
        raise HTTPException(404, "Pump not found")
    if pump.fuel_id!= data.fuel_id:
        raise HTTPException(400, "Pump fuel type mismatch")
    
    # Deduct stock
    fuel.actual_liters -= data.liters_sold
    session.add(fuel)
    
    # For now hardcode recorded_by=1, replace with actual cashier from JWT
    recorded_by_id = 1
    cashier = session.get(User, recorded_by_id)
    
    sale = Sale(
        pump_id=data.pump_id,
        attendant_name=data.attendant_name,
        recorded_by=recorded_by_id,
        liters_sold=data.liters_sold,
        price_per_liter=fuel.price,
        total_amount=data.liters_sold * fuel.price,
        payment_method=data.payment_method
    )
    session.add(sale)
    session.commit()
    session.refresh(sale)
    
    return SaleResponse(
        id=sale.id,
        fuel_name=fuel.name,
        pump_name=pump.name,
        attendant_name=sale.attendant_name,
        recorded_by=cashier.username,
        liters_sold=sale.liters_sold,
        price_per_liter=sale.price_per_liter,
        total_amount=sale.total_amount,
        payment_method=sale.payment_method,
        sold_at=sale.sold_at
    )

@router.get("/by-attendant/{attendant_name}", response_model=List[SaleResponse])
def get_sales_by_attendant(
    attendant_name: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    if attendant_name not in VALID_ATTENDANTS:
        raise HTTPException(400, "Invalid attendant name")
    
    query = select(Sale).where(Sale.attendant_name == attendant_name)
    
    if start_date:
        query = query.where(Sale.sold_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(Sale.sold_at <= datetime.combine(end_date, datetime.max.time()))
    
    sales = session.exec(query.order_by(Sale.sold_at.desc())).all()
    
    result = []
    for sale in sales:
        fuel = session.get(Fuel, sale.fuel_id)
        pump = session.get(Pump, sale.pump_id)
        cashier = session.get(User, sale.recorded_by)
        result.append(SaleResponse(
            id=sale.id,
            fuel_name=fuel.name,
            pump_name=pump.name,
            attendant_name=sale.attendant_name,
            recorded_by=cashier.username,
            liters_sold=sale.liters_sold,
            price_per_liter=sale.price_per_liter,
            total_amount=sale.total_amount,
            payment_method=sale.payment_method,
            sold_at=sale.sold_at
        ))
    return result

@router.get("/summary/by-attendant", response_model=List[AttendantSalesSummary])
def get_attendant_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    query = select(Sale)
    if start_date:
        query = query.where(Sale.sold_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(Sale.sold_at <= datetime.combine(end_date, datetime.max.time()))
    
    sales = session.exec(query).all()
    
    summary = {}
    for sale in sales:
        name = sale.attendant_name
        if name not in summary:
            summary[name] = {
                "attendant_name": name,
                "total_sales": 0.0,
                "total_liters": 0.0,
                "transaction_count": 0,
                "by_fuel": {}
            }
        
        summary[name]["total_sales"] += sale.total_amount
        summary[name]["total_liters"] += sale.liters_sold
        summary[name]["transaction_count"] += 1
        
        fuel = session.get(Fuel, sale.fuel_id)
        summary[name]["by_fuel"][fuel.name] = summary[name]["by_fuel"].get(fuel.name, 0) + sale.total_amount
    
    return list(summary.values())