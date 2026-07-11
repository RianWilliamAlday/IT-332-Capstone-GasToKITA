from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select,  and_, func
from..db.database import get_session, Sale, Fuel, User, Pump
from..models.schemas import SaleCreate, SaleResponse, AttendantSalesSummary, SaleHistoryItem, SalesHistoryResponse
from ..services.auth import get_current_user 
from datetime import datetime, date, time
from typing import List, Optional

router = APIRouter(prefix="/api/sales", tags=["sales"])

VALID_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]

@router.post("/", response_model=SaleResponse)
def create_sale(
    data: SaleCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if data.attendant_name not in VALID_ATTENDANTS:
        raise HTTPException(400, f"Invalid attendant. Must be one of {VALID_ATTENDANTS}")
    
    pump = session.get(Pump, data.pump_id)
    if not pump:
        raise HTTPException(404, "Pump not found")

    fuel_id = pump.fuel_type_id
    fuel = session.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")
    if fuel.actual_liters < data.liters_sold:
        raise HTTPException(400, f"Not enough stock. Only {fuel.actual_liters}L left")

    fuel.actual_liters -= data.liters_sold
    session.add(fuel)

    sale = Sale(
        fuel_id=fuel_id,
        pump_id=data.pump_id,
        attendant_name=data.attendant_name,
        recorded_by=current_user.id,
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
        recorded_by=current_user.name,
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
            recorded_by_name = cashier.name if cashier else "Unknown",
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

@router.get("/history", response_model=SalesHistoryResponse)
def get_sales_history(
    start_date: Optional[date] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="YYYY-MM-DD"),
    fuel_id: Optional[int] = Query(None),
    attendant_name: Optional[str] = Query(None),
    pump_id: Optional[int] = Query(None),
    payment_method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session)
):
    filters = []

    if start_date:
        filters.append(Sale.sold_at >= datetime.combine(start_date, time.min))
    if end_date:
        filters.append(Sale.sold_at <= datetime.combine(end_date, time.max))
    if fuel_id is not None:
        filters.append(Sale.fuel_id == fuel_id)
    if attendant_name:
        filters.append(Sale.attendant_name == attendant_name)
    if pump_id is not None:
        filters.append(Sale.pump_id == pump_id)
    if payment_method is not None:
        filters.append(Sale.payment_method == payment_method)

    query = select(Sale)
    if filters:
        query = query.where(and_(*filters))
    count_query = select(func.count()).select_from(Sale)
    total_query = select(
        func.sum(Sale.total_amount),
        func.sum(Sale.liters_sold)
    ).select_from(Sale)

    if filters:
        count_query = count_query.where(and_(*filters))
        total_query = total_query.where(and_(*filters))

    total_count = session.exec(count_query).one()
    total_amount, total_liters = session.exec(total_query).one()
    offset = (page - 1) * page_size
    sales = session.exec(
        query.order_by(Sale.sold_at.desc())
       .offset(offset)
       .limit(page_size)
    ).all()
    items = []
    for sale in sales:
        fuel = session.get(Fuel, sale.fuel_id)
        pump = session.get(Pump, sale.pump_id)
        cashier = session.get(User, sale.recorded_by)

        items.append(SaleHistoryItem(
            id=sale.id,
            fuel_id=sale.fuel_id,
            fuel_name=fuel.name if fuel else "Unknown",
            pump_id=sale.pump_id,
            pump_name=pump.name if pump else "Unknown",
            attendant_name=sale.attendant_name,
            liters_sold=sale.liters_sold,
            price_per_liter=sale.price_per_liter,
            total_amount=sale.total_amount,
            payment_method=sale.payment_method,
            sold_at=sale.sold_at,
            recorded_by=cashier.name if cashier else "Unknown"
        ))

    return SalesHistoryResponse(
        sales=items,
        total_count=total_count,
        total_amount=total_amount or 0.0,
        total_liters=total_liters or 0.0,
        page=page,
        page_size=page_size
    )

@router.get("/history/export")
def export_sales_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    from fastapi.responses import StreamingResponse
    import csv
    import io

    query = select(Sale)
    if start_date:
        query = query.where(Sale.sold_at >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.where(Sale.sold_at <= datetime.combine(end_date, time.max))

    sales = session.exec(query.order_by(Sale.sold_at.desc())).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Time", "Fuel", "Pump", "Attendant", "Liters",
        "Price/L", "Total", "Payment", "Recorded By"
    ])

    for sale in sales:
        fuel = session.get(Fuel, sale.fuel_id)
        pump = session.get(Pump, sale.pump_id)
        cashier = session.get(User, sale.recorded_by)
        writer.writerow([
            sale.sold_at.strftime("%Y-%m-%d"),
            sale.sold_at.strftime("%H:%M:%S"),
            fuel.name,
            pump.name,
            sale.attendant_name,
            f"{sale.liters_sold:.2f}",
            f"{sale.price_per_liter:.2f}",
            f"{sale.total_amount:.2f}",
            sale.payment_method,
            cashier.name if cashier else "Unknown"
        ])

    output.seek(0)
    filename = f"sales_{start_date or 'all'}_to_{end_date or 'all'}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/history/today")
def get_today_history(session: Session = Depends(get_session)):
    today = date.today()
    return get_sales_history(
        start_date=today,
        end_date=today,
        fuel_id=None,
        attendant_name=None,
        pump_id=None,
        payment_method=None,
        page=1,
        page_size=50,
        session=session
    )

@router.delete("/{sale_id}")
def void_sale(sale_id: int, session: Session = Depends(get_session)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Sale not found")
    fuel = session.get(Fuel, sale.fuel_id)
    if fuel:
        fuel.actual_liters += sale.liters_sold
        session.add(fuel)

    session.delete(sale)
    session.commit()

    return {"message": f"Sale {sale_id} voided. {sale.liters_sold}L returned to tank."}