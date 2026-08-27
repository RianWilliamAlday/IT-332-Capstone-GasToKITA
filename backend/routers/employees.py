from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from..db.database import get_session, Attendant, User, Sale, OilSale, Fuel, Pump, OilProduct
from datetime import datetime, date, time, timedelta
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/employees", tags=["Employees"])

class AttendantCreate(BaseModel):
    name: str
    employee_id: Optional[str] = None
    contact: Optional[str] = None

class AttendantUpdate(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/attendants")
def add_attendant(data: AttendantCreate, session: Session = Depends(get_session)):
    clean = data.name.strip()
    if session.exec(select(Attendant).where(func.lower(Attendant.name) == clean.lower())).first():
        raise HTTPException(400, f"'{clean}' already exists")
    att = Attendant(name=clean, employee_id=data.employee_id, contact=data.contact, is_active=True,
                    created_at=datetime.now(), updated_at=datetime.now())
    session.add(att); session.commit(); session.refresh(att)
    return att

@router.get("/cashiers")
def list_attendants(include_inactive: bool = False, search: str = None, session: Session = Depends(get_session)):
    q = select(Attendant)
    if not include_inactive: q = q.where(Attendant.is_active == True)
    if search: q = q.where(Attendant.name.ilike(f"%{search}%"))
    return session.exec(q.order_by(Attendant.name)).all()

@router.get("/attendants/active")
def list_active(session: Session = Depends(get_session)):
    return session.exec(select(Attendant).where(Attendant.is_active == True).order_by(Attendant.name)).all()

@router.get("/attendants/names")
def list_names(session: Session = Depends(get_session)):
    names = session.exec(select(Attendant.name).where(Attendant.is_active == True).order_by(Attendant.name)).all()
    return names if names else ["Attendant 1","Attendant 2","Attendant 3"]

@router.put("/attendants/{attendant_id}")
def update_attendant(attendant_id: int, data: AttendantUpdate, session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    if not att: raise HTTPException(404, "Not found")
    if data.name and data.name.strip().lower()!= att.name.lower():
        if session.exec(select(Attendant).where(func.lower(Attendant.name) == data.name.lower(), Attendant.id!= attendant_id)).first():
            raise HTTPException(400, "Name taken")
        att.name = data.name.strip()
    if data.contact is not None: att.contact = data.contact
    if data.employee_id is not None: att.employee_id = data.employee_id
    if data.is_active is not None:
        att.is_active = data.is_active
        att.deactivated_at = datetime.now() if not data.is_active else None
    att.updated_at = datetime.now()
    session.add(att); session.commit(); session.refresh(att)
    return att

@router.patch("/attendants/{attendant_id}/rename")
def rename_attendant(attendant_id: int, new_name: str = Query(...), session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    if not att: raise HTTPException(404, "Not found")
    clean = new_name.strip()
    if session.exec(select(Attendant).where(func.lower(Attendant.name) == clean.lower(), Attendant.id!= attendant_id)).first():
        raise HTTPException(400, "Name exists")
    att.name = clean; att.updated_at = datetime.now()
    session.add(att); session.commit(); session.refresh(att)
    return att

@router.patch("/attendants/{attendant_id}/deactivate")
def deactivate(attendant_id: int, session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    att.is_active = False; att.deactivated_at = datetime.now(); att.updated_at = datetime.now()
    session.add(att); session.commit()
    return {"message": f"{att.name} deactivated"}

@router.delete("/attendants/{attendant_id}")
def remove(attendant_id: int, force: bool = False, session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    cnt = session.exec(select(func.count()).select_from(Sale).where(Sale.attendant_name == att.name)).one()
    if cnt > 0 and not force:
        raise HTTPException(400, f"Has {cnt} sales - deactivate or use?force=true")
    session.delete(att); session.commit()
    return {"message": f"{att.name} removed"}

@router.post("/attendants/seed-defaults")
def seed(session: Session = Depends(get_session)):
    if session.exec(select(Attendant)).first(): return {"message": "already seeded"}
    for n in ["Attendant 1","Attendant 2","Attendant 3"]:
        session.add(Attendant(name=n, display_name=n, is_active=True, created_at=datetime.now(), updated_at=datetime.now()))
    session.commit()
    return {"message": "seeded"}

@router.get("/")
def list_cashiers(session: Session = Depends(get_session)):
    """List all user accounts that can be cashiers"""
    users = session.exec(select(User).order_by(User.name)).all()
    result = []
    for u in users:
        fuel_cnt = session.exec(select(func.count()).select_from(Sale).where(Sale.recorded_by == u.id)).one() or 0
        oil_cnt = session.exec(select(func.count()).select_from(OilSale).where(OilSale.sold_by == u.id)).one() or 0
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "total_sales_recorded": int(fuel_cnt + oil_cnt)
        })
    return result

@router.get("/{user_id}/history")
def get_cashier_history(
    user_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    product_type: Optional[str] = Query(None, description="fuel, oil, all"),
    attendant_name: Optional[str] = Query(None, description="Filter by attendant on duty"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, f"Cashier account {user_id} not found")

    fuel_filters = [Sale.recorded_by == user_id]
    oil_filters = [OilSale.sold_by == user_id]

    if start_date:
        fuel_filters.append(Sale.sold_at >= datetime.combine(start_date, time.min))
        oil_filters.append(OilSale.sold_at >= datetime.combine(start_date, time.min))
    if end_date:
        fuel_filters.append(Sale.sold_at <= datetime.combine(end_date, time.max))
        oil_filters.append(OilSale.sold_at <= datetime.combine(end_date, time.max))
    if attendant_name:
        fuel_filters.append(Sale.attendant_name == attendant_name)
        oil_filters.append(OilSale.attendant_name == attendant_name)

    fuel_sales = []
    oil_sales = []
    if product_type in (None, "all", "fuel"):
        fuel_sales = session.exec(select(Sale).where(*fuel_filters).order_by(Sale.sold_at.desc())).all()
    if product_type in (None, "all", "oil"):
        oil_sales = session.exec(select(OilSale).where(*oil_filters).order_by(OilSale.sold_at.desc())).all()

    unified = []
    for s in fuel_sales:
        fuel = session.get(Fuel, s.fuel_id)
        pump = session.get(Pump, s.pump_id)
        unified.append({
            "id": s.id, "product_type": "fuel",
            "product_name": fuel.name if fuel else "Fuel",
            "attendant_name": s.attendant_name,
            "quantity": s.liters_sold, "unit": "L",
            "price": s.price_per_liter, "total": s.total_amount,
            "payment": s.payment_method,
            "pump": pump.name if pump else None,
            "sold_at": s.sold_at,
            "recorded_by": user.name
        })
    for s in oil_sales:
        oil = session.get(OilProduct, s.oil_product_id)
        unified.append({
            "id": s.id, "product_type": "oil",
            "product_name": f"{oil.brand} {oil.name}" if oil else "Oil",
            "attendant_name": s.attendant_name,
            "quantity": float(s.quantity), "unit": "pcs",
            "price": s.price_per_unit, "total": s.total_amount,
            "payment": s.payment_method,
            "pump": None,
            "sold_at": s.sold_at,
            "recorded_by": user.name
        })

    unified.sort(key=lambda x: x["sold_at"], reverse=True)

    total = sum(x["total"] for x in unified)
    by_attendant = {}
    for x in unified:
        by_attendant[x["attendant_name"]] = by_attendant.get(x["attendant_name"], 0) + x["total"]

    offset = (page-1)*page_size
    paged = unified[offset:offset+page_size]

    return {
        "cashier": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        "summary": {
            "total_transactions": len(unified),
            "total_amount": round(total,2),
            "fuel_tx": len(fuel_sales),
            "oil_tx": len(oil_sales),
            "by_attendant": by_attendant,
            "period": f"{start_date or 'all'} to {end_date or 'all'}"
        },
        "sales": paged,
        "page": page, "page_size": page_size, "total_count": len(unified)
    }

@router.get("/{user_id}/summary")
def get_cashier_summary(user_id: int, days: int = Query(30), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user: raise HTTPException(404, "Cashier not found")
    since = datetime.now() - timedelta(days=days)

    fuels = session.exec(select(Sale).where(Sale.recorded_by == user_id, Sale.sold_at >= since)).all()
    oils = session.exec(select(OilSale).where(OilSale.sold_by == user_id, OilSale.sold_at >= since)).all()

    return {
        "cashier": user.name,
        "period_days": days,
        "fuel": {"tx": len(fuels), "liters": round(sum(s.liters_sold for s in fuels),2), "revenue": round(sum(s.total_amount for s in fuels),2)},
        "oil": {"tx": len(oils), "qty": sum(s.quantity for s in oils), "revenue": round(sum(s.total_amount for s in oils),2)},
        "total_revenue": round(sum(s.total_amount for s in fuels+oils),2),
        "unique_attendants_handled": len(set(s.attendant_name for s in fuels+oils))
    }

@router.get("/history/all")
def get_all_cashiers_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """For defense: compare cashiers if you have 2 shifts"""
    users = session.exec(select(User)).all()
    result = []
    for u in users:
        f_filters = [Sale.recorded_by == u.id]
        o_filters = [OilSale.sold_by == u.id]
        if start_date:
            f_filters.append(Sale.sold_at >= datetime.combine(start_date, time.min))
            o_filters.append(OilSale.sold_at >= datetime.combine(start_date, time.min))
        if end_date:
            f_filters.append(Sale.sold_at <= datetime.combine(end_date, time.max))
            o_filters.append(OilSale.sold_at <= datetime.combine(end_date, time.max))

        f_cnt = session.exec(select(func.count()).select_from(Sale).where(*f_filters)).one() or 0
        o_cnt = session.exec(select(func.count()).select_from(OilSale).where(*o_filters)).one() or 0
        f_rev = session.exec(select(func.sum(Sale.total_amount)).where(*f_filters)).one() or 0
        o_rev = session.exec(select(func.sum(OilSale.total_amount)).where(*o_filters)).one() or 0

        result.append({
            "cashier_id": u.id,
            "cashier_name": u.name,
            "transactions": int(f_cnt+o_cnt),
            "revenue": round(float(f_rev+o_rev),2)
        })
    result.sort(key=lambda x: x["revenue"], reverse=True)
    return result