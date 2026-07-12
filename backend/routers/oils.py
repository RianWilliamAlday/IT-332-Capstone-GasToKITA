from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from ..db.database import get_session, OilProduct, OilRestockLog, OilSale

router = APIRouter(prefix="/oils", tags=["Oil / Products"])

class OilCreate(BaseModel):
    brand: str
    name: str
    variant: Optional[str] = None
    stock: int = 0
    price: float
    cost: float = 0
    low_stock_threshold: int = 5

class OilRestockRequest(BaseModel):
    quantity_added: int
    total_cost: float
    supplier: Optional[str] = None

class OilSellRequest(BaseModel):
    quantity: int
    payment_method: str = "cash"
    attendant_name: Optional[str] = "admin"

@router.post("/", response_model=OilProduct)
def create_oil(data: OilCreate, session: Session = Depends(get_session)):
    oil = OilProduct(**data.model_dump(), updated_at=datetime.now())
    session.add(oil)
    session.commit()
    session.refresh(oil)
    return oil

@router.get("/{oil_id}", response_model=OilProduct)
def get_oil(oil_id: int, session: Session = Depends(get_session)):
    oil = session.get(OilProduct, oil_id)
    if not oil: raise HTTPException(404, "Oil product not found")
    return oil

@router.put("/{oil_id}", response_model=OilProduct)
def update_oil(oil_id: int, data: OilCreate, session: Session = Depends(get_session)):
    oil = session.get(OilProduct, oil_id)
    if not oil: raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(oil, k, v)
    oil.updated_at = datetime.now()
    session.add(oil)
    session.commit()
    session.refresh(oil)
    return oil

@router.post("/{oil_id}/restock")
def restock_oil(oil_id: int, data: OilRestockRequest, session: Session = Depends(get_session)):
    oil = session.get(OilProduct, oil_id)
    if not oil: raise HTTPException(404, "Oil product not found")
    if data.quantity_added <= 0: raise HTTPException(400, "Quantity must be positive")

    oil.stock += data.quantity_added
    if data.quantity_added > 0:
        oil.cost = data.total_cost / data.quantity_added
    oil.supplier = data.supplier or oil.supplier
    oil.updated_at = datetime.now()

    log = OilRestockLog(
        oil_product_id=oil.id,
        quantity_added=data.quantity_added,
        total_cost=data.total_cost,
        supplier=data.supplier
    )
    session.add(oil)
    session.add(log)
    session.commit()
    session.refresh(oil)

    return {
        "message": f"Restocked {data.quantity_added} pcs of {oil.brand} {oil.name}",
        "new_stock": oil.stock,
        "needs_restock": oil.stock <= oil.low_stock_threshold
    }

@router.post("/{oil_id}/sell")
def sell_oil(oil_id: int, data: OilSellRequest, session: Session = Depends(get_session)):
    oil = session.get(OilProduct, oil_id)
    if not oil: raise HTTPException(404, "Oil product not found")
    if data.quantity <= 0: raise HTTPException(400, "Quantity must be positive")
    if oil.stock < data.quantity:
        raise HTTPException(400, f"Insufficient stock. Only {oil.stock} left")

    total = data.quantity * oil.price
    oil.stock -= data.quantity
    oil.updated_at = datetime.now()

    sale = OilSale(
        oil_product_id=oil.id,
        quantity=data.quantity,
        price_per_unit=oil.price,
        total_amount=total,
        payment_method=data.payment_method,
        attendant_name=data.attendant_name
    )

    session.add(oil)
    session.add(sale)
    session.commit()
    session.refresh(sale)

    return {
        "message": f"Sold {data.quantity} x {oil.brand} {oil.name}",
        "sale_id": sale.id,
        "total_amount": total,
        "remaining_stock": oil.stock,
        "low_stock_alert": oil.stock <= oil.low_stock_threshold
    }

@router.get("/sales/history", response_model=List[OilSale])
def oil_sales_history(days: int = 30, session: Session = Depends(get_session)):
    since = datetime.now() - timedelta(days=days)
    return session.exec(select(OilSale).where(OilSale.sold_at >= since).order_by(OilSale.sold_at.desc())).all()