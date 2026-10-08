from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select, func
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel
from..db.database import get_session, Sale, Fuel, Pump, FuelBatch, FuelSaleBatch, OilProduct, OilSale, Attendant, User
from..services.gcashService import create_gcash_checkout, retrieve_checkout
from..services.auth import get_current_user

router = APIRouter(prefix="/api/payments", tags=["GCash Payments"])
ProductType = Literal["fuel", "oil"]

class GCashDialogRequest(BaseModel):
    product_type: ProductType = "fuel"
    pump_id: Optional[int] = None
    fuel_id: Optional[int] = None
    liters_sold: Optional[float] = None
    oil_product_id: Optional[int] = None
    quantity: Optional[int] = None
    attendant_name: str

def get_fifo_batches(session: Session, fuel_id: int):
    return session.exec(select(FuelBatch).where(FuelBatch.fuel_id == fuel_id, FuelBatch.liters_remaining > 0).order_by(FuelBatch.restocked_at.asc(), FuelBatch.id.asc())).all()

@router.post("/gcash/dialog-checkout")
def create_dialog_checkout(
    data: GCashDialogRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    clean = data.attendant_name.strip()
    att = session.exec(select(Attendant).where(func.lower(Attendant.name) == clean.lower(), Attendant.is_active == True)).first()
    if not att:
        cnt = session.exec(select(func.count()).select_from(Attendant)).one()
        if cnt!= 0:
            active_names = session.exec(select(Attendant.name).where(Attendant.is_active == True)).all()
            raise HTTPException(400, f"Invalid attendant '{data.attendant_name}'. Must be one of {active_names}")

    total_amount = 0
    description = ""
    sale = None
    oil_sale = None

    if data.product_type == "fuel":
        if not data.liters_sold or data.liters_sold <= 0:
            raise HTTPException(400, "Liters must be > 0")
        fuel = None
        pump = None
        if data.pump_id:
            pump = session.get(Pump, data.pump_id)
            if not pump: raise HTTPException(404, "Pump not found")
            fuel = session.get(Fuel, pump.fuel_type_id)
        elif data.fuel_id:
            fuel = session.get(Fuel, data.fuel_id)
        else:
            raise HTTPException(400, "Need pump_id or fuel_id")
        if not fuel: raise HTTPException(404, "Fuel not found")

        batches = get_fifo_batches(session, fuel.id)
        total_avail = sum(b.liters_remaining for b in batches)
        if total_avail < data.liters_sold:
            raise HTTPException(400, f"Not enough stock. Only {total_avail:.2f}L, requested {data.liters_sold}L")

        liters_needed = data.liters_sold
        for b in batches:
            if liters_needed <= 0: break
            take = min(b.liters_remaining, liters_needed)
            total_amount += take * b.selling_price
            liters_needed -= take
        total_amount = round(total_amount, 2)
        description = f"{fuel.name} {data.liters_sold}L"

        sale = Sale(
            fuel_id=fuel.id,
            pump_id=pump.id if pump else None,
            attendant_name=data.attendant_name,
            recorded_by=current_user.id,
            liters_sold=data.liters_sold,
            price_per_liter=round(total_amount / data.liters_sold, 2),
            total_amount=total_amount,
            amount_paid=0,
            change_given=0,
            receipt_no="PENDING",
            payment_method="gcash",
            payment_status="pending"
        )
        session.add(sale)
        session.flush()

    else:
        if not data.oil_product_id or not data.quantity:
            raise HTTPException(400, "Need oil_product_id and quantity")
        oil = session.get(OilProduct, data.oil_product_id)
        if not oil: raise HTTPException(404, "Oil not found")
        if oil.stock < data.quantity:
            raise HTTPException(400, f"Not enough oil stock. Only {oil.stock} pcs")
        total_amount = round(oil.price * data.quantity, 2)
        description = f"{oil.brand} {oil.name} x{data.quantity}"

        oil_sale = OilSale(
            oil_product_id=oil.id,
            quantity=data.quantity,
            price_per_unit=oil.price,
            total_amount=total_amount,
            amount_paid=0,
            change_given=0,
            receipt_no="PENDING",
            payment_method="gcash",
            payment_status="pending",
            sold_by=current_user.id,
            attendant_name=data.attendant_name
        )
        session.add(oil_sale)
        session.flush()

    ref_id = f"{data.product_type}-{(sale.id if sale else oil_sale.id)}-{datetime.now().strftime('%H%M%S')}"
    try:
        checkout = create_gcash_checkout(
            amount_php=total_amount,
            description=description,
            reference_id=ref_id,
            metadata={
                "product_type": data.product_type,
                "sale_id": str(sale.id if sale else ""),
                "oil_sale_id": str(oil_sale.id if oil_sale else ""),
                "attendant": data.attendant_name
            }
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"PayMongo error: {str(e)}")

    if sale:
        sale.paymongo_checkout_id = checkout['checkout_id']
        sale.receipt_no = f"F-{sale.sold_at.strftime('%y%m%d')}-{sale.id:06d}-GCASH-PENDING"
        session.add(sale)
    if oil_sale:
        oil_sale.paymongo_checkout_id = checkout['checkout_id']
        oil_sale.receipt_no = f"O-{oil_sale.sold_at.strftime('%y%m%d')}-{oil_sale.id:06d}-GCASH-PENDING"
        session.add(oil_sale)

    session.commit()
    if sale: session.refresh(sale)
    if oil_sale: session.refresh(oil_sale)

    return {
        "sale_id": sale.id if sale else None,
        "oil_sale_id": oil_sale.id if oil_sale else None,
        "product_type": data.product_type,
        "checkout_id": checkout['checkout_id'],
        "checkout_url": checkout['checkout_url'],
        "total_amount": total_amount,
        "status": "pending"
    }

@router.get("/gcash/status/{checkout_id}")
def check_status(checkout_id: str, session: Session = Depends(get_session)):
    try:
        info = retrieve_checkout(checkout_id)
    except Exception as e:
        raise HTTPException(500, str(e))

    sale = session.exec(select(Sale).where(Sale.paymongo_checkout_id == checkout_id)).first()
    oil_sale = None
    if not sale:
        oil_sale = session.exec(select(OilSale).where(OilSale.paymongo_checkout_id == checkout_id)).first()

    return {
        "checkout_id": checkout_id,
        "is_paid": info["is_paid"],
        "sale_id": sale.id if sale else (oil_sale.id if oil_sale else None),
        "product_type": "fuel" if sale else ("oil" if oil_sale else None),
        "payment_status": (sale.payment_status if sale else (oil_sale.payment_status if oil_sale else 'not_found')),
        "paymongo": info["payments"]
    }

@router.post("/gcash/manual-confirm/{sale_id}")
def manual_confirm(sale_id: int, product_type: ProductType = "fuel", gcash_ref: str = None, session: Session = Depends(get_session)):
    if product_type == "fuel":
        sale = session.get(Sale, sale_id)
        if not sale: raise HTTPException(404, "Sale not found")
        if sale.payment_status == 'paid':
            return {"message": "Already paid", "sale_id": sale_id}

        fuel = session.get(Fuel, sale.fuel_id)
        batches = get_fifo_batches(session, fuel.id)
        liters_needed = sale.liters_sold
        for batch in batches:
            if liters_needed <= 0: break
            take = min(batch.liters_remaining, liters_needed)
            batch.liters_remaining -= take
            fsb = FuelSaleBatch(sale_id=sale.id, batch_id=batch.id, liters_consumed=take, price_per_liter=batch.selling_price, total_amount=round(take*batch.selling_price,2))
            session.add(fsb)
            session.add(batch)
            liters_needed -= take

        remaining = get_fifo_batches(session, fuel.id)
        fuel.actual_liters = sum(b.liters_remaining for b in remaining)
        session.add(fuel)
        sale.payment_status = 'paid'
        sale.amount_paid = sale.total_amount
        if gcash_ref: sale.gcash_ref_no = gcash_ref
        sale.receipt_no = sale.receipt_no.replace("PENDING", "PAID")
        session.add(sale)
        session.commit()
        return {"message": "Fuel sale confirmed PAID", "sale_id": sale_id, "receipt_no": sale.receipt_no}
    else:
        sale = session.get(OilSale, sale_id)
        if not sale: raise HTTPException(404, "Oil sale not found")
        oil = session.get(OilProduct, sale.oil_product_id)
        oil.stock -= sale.quantity
        session.add(oil)
        sale.payment_status = 'paid'
        sale.amount_paid = sale.total_amount
        sale.receipt_no = sale.receipt_no.replace("PENDING", "PAID")
        session.add(sale)
        session.commit()
        return {"message": "Oil sale confirmed PAID", "sale_id": sale_id}

@router.post("/webhooks/paymongo")
async def webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.json()
    data = payload.get("data", {})
    attr = data.get("attributes", {})
    event_type = attr.get("type")
    if event_type == "checkout_session.payment.paid":
        checkout_data = attr.get("data", {})
        checkout_id = checkout_data.get("id")
        sale = session.exec(select(Sale).where(Sale.paymongo_checkout_id == checkout_id)).first()
        if sale:
            return manual_confirm(sale.id, "fuel")
        oil_sale = session.exec(select(OilSale).where(OilSale.paymongo_checkout_id == checkout_id)).first()
        if oil_sale:
            return manual_confirm(oil_sale.id, "oil")
    return {"status": "ignored", "type": event_type}