from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_, func
from ..db.database import get_session, Sale, Fuel, User, Pump, OilProduct, OilSale, FuelBatch, FuelSaleBatch
from ..models.schemas import (
    SaleCreate, SaleResponse, SaleHistoryItem, SalesHistoryResponse,
    OilSaleCreate, OilSaleResponse, OilSaleHistoryItem, OilSalesHistoryResponse,
    UnifiedSaleItem, UnifiedHistoryResponse, ProductType,
    FifoSaleDetail
)
from ..services.auth import get_current_user
from datetime import datetime, date, time
from typing import List, Optional

router = APIRouter(prefix="/api/sales", tags=["Centralized Sales"])

VALID_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]

def get_fifo_batches(session: Session, fuel_id: int):
    return session.exec(select(FuelBatch).where(FuelBatch.fuel_id == fuel_id, FuelBatch.liters_remaining > 0).order_by(FuelBatch.restocked_at.asc(), FuelBatch.id.asc())).all()

def ensure_initial_batch(session: Session, fuel: Fuel):
    existing = session.exec(select(FuelBatch).where(FuelBatch.fuel_id == fuel.id)).first()
    if not existing and fuel.actual_liters > 0:
        batch = FuelBatch(
            fuel_id=fuel.id,
            liters_initial=fuel.actual_liters,
            liters_remaining=fuel.actual_liters,
            cost_per_liter=fuel.price * 0.8,
            selling_price=fuel.price,
            supplier="Initial Stock",
            restocked_by="system",
            restocked_at=fuel.last_restocked or datetime.now()
        )
        session.add(batch)
        session.commit()
        return batch
    return existing

def get_current_fifo_price(session: Session, fuel_id: int, fuel_fallback: Fuel = None):
    batches = get_fifo_batches(session, fuel_id)
    if batches:
        return batches[0].selling_price
    return fuel_fallback.price if fuel_fallback else 0.0

@router.post("/fuel", response_model=SaleResponse)
def create_fuel_sale(
    data: SaleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if data.attendant_name not in VALID_ATTENDANTS:
        raise HTTPException(400, f"Invalid attendant. Must be one of {VALID_ATTENDANTS}")
    pump = session.get(Pump, data.pump_id)
    if not pump:
        raise HTTPException(404, "Pump not found")
    fuel = session.get(Fuel, pump.fuel_type_id)
    if not fuel:
        raise HTTPException(404, "Fuel type not found")

    ensure_initial_batch(session, fuel)

    batches = get_fifo_batches(session, fuel.id)
    total_available = sum(b.liters_remaining for b in batches)
    if total_available < data.liters_sold:
        raise HTTPException(400, f"Not enough stock (FIFO). Only {total_available:.2f}L available across {len(batches)} batches, requested {data.liters_sold}L")

    liters_needed = data.liters_sold
    consumptions = []
    total_amount = 0.0

    for batch in batches:
        if liters_needed <= 0:
            break
        take = min(batch.liters_remaining, liters_needed)
        batch.liters_remaining -= take
        total_amount += take * batch.selling_price
        consumptions.append((batch, take, batch.selling_price))
        liters_needed -= take
        session.add(batch)

    if liters_needed > 0.001:
        raise HTTPException(400, "FIFO consumption failed - not enough batch stock")

    weighted_avg_price = total_amount / data.liters_sold if data.liters_sold > 0 else 0
    total_amount = round(total_amount, 2)

    if data.amount_paid < total_amount - 0.01:
        raise HTTPException(400, f"Amount paid P{data.amount_paid:.2f} is less than due P{total_amount:.2f}")
    
    change_given = round(data.amount_paid - total_amount, 2)

    sale = Sale(
        fuel_id=fuel.id,
        pump_id=data.pump_id,
        attendant_name=data.attendant_name,
        recorded_by=current_user.id,
        liters_sold=data.liters_sold,
        price_per_liter=round(weighted_avg_price, 2),
        total_amount=total_amount,
        amount_paid=round(data.amount_paid, 2),
        change_given=change_given,
        receipt_no="TMP",
        payment_method=data.payment_method
    )
    session.add(sale)
    session.flush()

    sale.receipt_no = f"F-{sale.sold_at.strftime('%y%m%d')}-{sale.id:06d}"
    session.add(sale)

    fifo_details = []
    for batch, take, price in consumptions:
        fsb = FuelSaleBatch(
            sale_id=sale.id,
            batch_id=batch.id,
            liters_consumed=take,
            price_per_liter=price,
            total_amount=round(take * price, 2)
        )
        session.add(fsb)
        fifo_details.append(FifoSaleDetail(
            batch_id=batch.id,
            liters_consumed=take,
            price_per_liter=price,
            total_amount=round(take * price, 2),
            restocked_at=batch.restocked_at
        ))

    remaining_batches = get_fifo_batches(session, fuel.id)
    fuel.actual_liters = sum(b.liters_remaining for b in remaining_batches)
    fuel.price = remaining_batches[0].selling_price if remaining_batches else weighted_avg_price
    session.add(fuel)

    session.commit()
    session.refresh(sale)

    return SaleResponse(
        id=sale.id,
        product_type="fuel",
        fuel_name=fuel.name,
        pump_name=pump.name,
        attendant_name=sale.attendant_name,
        recorded_by=current_user.name,
        liters_sold=sale.liters_sold,
        price_per_liter=sale.price_per_liter,
        total_amount=sale.total_amount,
        amount_paid=sale.amount_paid,
        change_given=sale.change_given,
        receipt_no=sale.receipt_no,
        payment_method=sale.payment_method,
        sold_at=sale.sold_at,
        fifo_breakdown=fifo_details,
        is_split_price=len(fifo_details) > 1
    )

@router.post("/oil", response_model=OilSaleResponse)
def create_oil_sale(
    data: OilSaleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    oil = session.get(OilProduct, data.oil_id)
    if not oil:
        raise HTTPException(404, "Oil product not found")
    if data.quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")
    if oil.stock < data.quantity:
        raise HTTPException(400, f"Insufficient stock. Only {oil.stock} left")
    attendant = data.attendant_name or current_user.name
    total = round(data.quantity * oil.price, 2)
    
    if data.amount_paid < total - 0.01:
        raise HTTPException(400, f"Amount paid P{data.amount_paid:.2f} is less than due P{total:.2f}")
    
    change_given = round(data.amount_paid - total, 2)
    
    oil.stock -= data.quantity
    session.add(oil)
    sale = OilSale(
        oil_product_id=oil.id,
        quantity=data.quantity,
        price_per_unit=oil.price,
        total_amount=total,
        amount_paid=round(data.amount_paid, 2),
        change_given=change_given,
        receipt_no="TMP",
        payment_method=data.payment_method,
        attendant_name=attendant,
        sold_by=current_user.id
    )
    session.add(sale)
    session.flush()
    sale.receipt_no = f"O-{sale.sold_at.strftime('%y%m%d')}-{sale.id:06d}"
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return OilSaleResponse(
        id=sale.id,
        product_type="oil",
        product_name=f"{oil.brand} {oil.name}",
        brand=oil.brand,
        quantity=sale.quantity,
        price_per_unit=sale.price_per_unit,
        total_amount=sale.total_amount,
        amount_paid=sale.amount_paid,
        change_given=sale.change_given,
        receipt_no=sale.receipt_no,
        payment_method=sale.payment_method,
        attendant_name=sale.attendant_name,
        sold_at=sale.sold_at,
        recorded_by=current_user.name,
        remaining_stock=oil.stock
    )

@router.get("/history/fuel", response_model=SalesHistoryResponse)
def get_fuel_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    fuel_id: Optional[int] = None,
    attendant_name: Optional[str] = None,
    pump_id: Optional[int] = None,
    payment_method: Optional[str] = None,
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
    if payment_method:
        filters.append(Sale.payment_method == payment_method)
    base_q = select(Sale)
    count_q = select(func.count()).select_from(Sale)
    total_q = select(func.sum(Sale.total_amount), func.sum(Sale.liters_sold)).select_from(Sale)
    if filters:
        base_q = base_q.where(and_(*filters))
        count_q = count_q.where(and_(*filters))
        total_q = total_q.where(and_(*filters))
    total_count = session.exec(count_q).one()
    total_amount, total_liters = session.exec(total_q).one()
    sales = session.exec(base_q.order_by(Sale.sold_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    items = []
    for s in sales:
        fuel = session.get(Fuel, s.fuel_id)
        pump = session.get(Pump, s.pump_id)
        user = session.get(User, s.recorded_by)
        batches = session.exec(select(FuelSaleBatch).where(FuelSaleBatch.sale_id == s.id)).all()
        fifo = [FifoSaleDetail(batch_id=b.batch_id, liters_consumed=b.liters_consumed, price_per_liter=b.price_per_liter, total_amount=b.total_amount) for b in batches] if batches else None
        items.append(SaleHistoryItem(
            id=s.id,
            sold_at=s.sold_at,
            fuel_id=s.fuel_id,
            pump_id=s.pump_id,
            attendant_name=s.attendant_name,
            liters_sold=s.liters_sold,
            price_per_liter=s.price_per_liter,
            total_amount=s.total_amount,
            amount_paid=getattr(s, 'amount_paid', s.total_amount),
            change_given=getattr(s, 'change_given', 0),
            receipt_no=getattr(s, 'receipt_no', None),
            payment_method=s.payment_method,
            recorded_by=user.name if user else "Unknown",
            fuel_name=fuel.name if fuel else "Unknown",
            pump_name=pump.name if pump else "Unknown",
            fifo_breakdown=fifo
        ))
    return SalesHistoryResponse(
        sales=items,
        total_count=total_count,
        total_amount=total_amount or 0.0,
        total_liters=total_liters or 0.0,
        page=page,
        page_size=page_size
    )

@router.get("/history/oil", response_model=OilSalesHistoryResponse)
def get_oil_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    oil_id: Optional[int] = None,
    attendant_name: Optional[str] = None,
    payment_method: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session)
):
    filters = []
    if start_date:
        filters.append(OilSale.sold_at >= datetime.combine(start_date, time.min))
    if end_date:
        filters.append(OilSale.sold_at <= datetime.combine(end_date, time.max))
    if oil_id:
        filters.append(OilSale.oil_product_id == oil_id)
    if attendant_name:
        filters.append(OilSale.attendant_name == attendant_name)
    if payment_method:
        filters.append(OilSale.payment_method == payment_method)
    base_q = select(OilSale)
    count_q = select(func.count()).select_from(OilSale)
    total_q = select(func.sum(OilSale.total_amount), func.sum(OilSale.quantity)).select_from(OilSale)
    if filters:
        base_q = base_q.where(and_(*filters))
        count_q = count_q.where(and_(*filters))
        total_q = total_q.where(and_(*filters))
    total_count = session.exec(count_q).one()
    total_amount, total_qty = session.exec(total_q).one()
    sales = session.exec(base_q.order_by(OilSale.sold_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    items = []
    for s in sales:
        oil = session.get(OilProduct, s.oil_product_id)
        user = session.get(User, s.sold_by) if s.sold_by else None
        items.append(OilSaleHistoryItem(
            id=s.id,
            oil_product_id=s.oil_product_id,
            product_name=f"{oil.brand} {oil.name}" if oil else "Unknown",
            brand=oil.brand if oil else "Unknown",
            quantity=s.quantity,
            price_per_unit=s.price_per_unit,
            total_amount=s.total_amount,
            amount_paid=getattr(s, 'amount_paid', s.total_amount),
            change_given=getattr(s, 'change_given', 0),
            receipt_no=getattr(s, 'receipt_no', None),
            payment_method=s.payment_method,
            attendant_name=s.attendant_name or "Unknown",
            sold_at=s.sold_at,
            recorded_by=user.name if user else "Unknown"
        ))
    return OilSalesHistoryResponse(
        sales=items,
        total_count=total_count,
        total_amount=total_amount or 0.0,
        total_quantity=total_qty or 0,
        page=page,
        page_size=page_size
    )

@router.get("/history", response_model=UnifiedHistoryResponse)
def get_unified_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_type: Optional[ProductType] = None,
    attendant_name: Optional[str] = None,
    payment_method: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session)
):
    fuel_filters = []
    oil_filters = []
    if start_date:
        fuel_filters.append(Sale.sold_at >= datetime.combine(start_date, time.min))
        oil_filters.append(OilSale.sold_at >= datetime.combine(start_date, time.min))
    if end_date:
        fuel_filters.append(Sale.sold_at <= datetime.combine(end_date, time.max))
        oil_filters.append(OilSale.sold_at <= datetime.combine(end_date, time.max))
    if attendant_name:
        fuel_filters.append(Sale.attendant_name == attendant_name)
        oil_filters.append(OilSale.attendant_name == attendant_name)
    if payment_method:
        fuel_filters.append(Sale.payment_method == payment_method)
        oil_filters.append(OilSale.payment_method == payment_method)
    fuel_sales = []
    oil_sales = []
    if product_type is None or product_type == ProductType.FUEL:
        fq = select(Sale)
        if fuel_filters:
            fq = fq.where(and_(*fuel_filters))
        fuel_sales = session.exec(fq.order_by(Sale.sold_at.desc())).all()
    if product_type is None or product_type == ProductType.OIL:
        oq = select(OilSale)
        if oil_filters:
            oq = oq.where(and_(*oil_filters))
        oil_sales = session.exec(oq.order_by(OilSale.sold_at.desc())).all()
    unified: List[UnifiedSaleItem] = []
    for s in fuel_sales:
        fuel = session.get(Fuel, s.fuel_id)
        pump = session.get(Pump, s.pump_id)
        user = session.get(User, s.recorded_by)
        unified.append(UnifiedSaleItem(
            id=s.id,
            product_type=ProductType.FUEL,
            product_name=fuel.name if fuel else "Fuel",
            quantity=s.liters_sold,
            unit="L",
            price_per_unit=s.price_per_liter,
            total_amount=s.total_amount,
            amount_paid=getattr(s, 'amount_paid', s.total_amount),
            change_given=getattr(s, 'change_given', 0),
            receipt_no=getattr(s, 'receipt_no', None),
            payment_method=s.payment_method,
            attendant_name=s.attendant_name,
            sold_at=s.sold_at,
            recorded_by=user.name if user else "Unknown",
            fuel_id=s.fuel_id,
            pump_id=s.pump_id,
            pump_name=pump.name if pump else None
        ))
    for s in oil_sales:
        oil = session.get(OilProduct, s.oil_product_id)
        user = session.get(User, s.sold_by) if s.sold_by else None
        unified.append(UnifiedSaleItem(
            id=s.id,
            product_type=ProductType.OIL,
            product_name=f"{oil.brand} {oil.name}" if oil else "Oil",
            quantity=float(s.quantity),
            unit="pcs",
            price_per_unit=s.price_per_unit,
            total_amount=s.total_amount,
            amount_paid=getattr(s, 'amount_paid', s.total_amount),
            change_given=getattr(s, 'change_given', 0),
            receipt_no=getattr(s, 'receipt_no', None),
            payment_method=s.payment_method,
            attendant_name=s.attendant_name or "Unknown",
            sold_at=s.sold_at,
            recorded_by=user.name if user else "Unknown",
            oil_id=s.oil_product_id,
            brand=oil.brand if oil else None
        ))
    unified.sort(key=lambda x: x.sold_at, reverse=True)
    total_count = len(unified)
    total_amount = sum(x.total_amount for x in unified)
    total_liters = sum(x.quantity for x in unified if x.product_type == ProductType.FUEL)
    total_oil_pcs = int(sum(x.quantity for x in unified if x.product_type == ProductType.OIL))
    offset = (page-1)*page_size
    paged = unified[offset:offset+page_size]
    return UnifiedHistoryResponse(
        sales=paged,
        total_count=total_count,
        total_amount=round(total_amount,2),
        total_liters=round(total_liters,2),
        total_oil_pcs=total_oil_pcs,
        page=page,
        page_size=page_size
    )

@router.delete("/{sale_id}")
def void_sale(
    sale_id: int,
    product_type: ProductType = Query(..., description="fuel or oil"),
    session: Session = Depends(get_session)
):
    if product_type == ProductType.FUEL:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise HTTPException(404, "Fuel sale not found")
        sale_batches = session.exec(select(FuelSaleBatch).where(FuelSaleBatch.sale_id == sale_id)).all()
        for sb in sale_batches:
            batch = session.get(FuelBatch, sb.batch_id)
            if batch:
                batch.liters_remaining += sb.liters_consumed
                session.add(batch)
            session.delete(sb)
        fuel = session.get(Fuel, sale.fuel_id)
        if fuel:
            remaining_batches = session.exec(select(FuelBatch).where(FuelBatch.fuel_id == fuel.id, FuelBatch.liters_remaining > 0)).all()
            fuel.actual_liters = sum(b.liters_remaining for b in remaining_batches)
            if remaining_batches:
                remaining_batches_sorted = sorted(remaining_batches, key=lambda b: b.restocked_at)
                fuel.price = remaining_batches_sorted[0].selling_price
            session.add(fuel)
        session.delete(sale)
        session.commit()
        return {"message": f"Fuel sale {sale_id} voided (FIFO restored). {sale.liters_sold}L returned to batches."}
    else:
        sale = session.get(OilSale, sale_id)
        if not sale:
            raise HTTPException(404, "Oil sale not found")
        oil = session.get(OilProduct, sale.oil_product_id)
        if oil:
            oil.stock += sale.quantity
            session.add(oil)
        session.delete(sale)
        session.commit()
        return {"message": f"Oil sale {sale_id} voided. {sale.quantity} pcs returned."}

@router.get("/history/export")
def export_unified_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_type: Optional[ProductType] = None,
    session: Session = Depends(get_session)
):
    from fastapi.responses import StreamingResponse
    import csv, io
    data = get_unified_history(start_date, end_date, product_type, None, None, 1, 10000, session)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Time","Type","Product","Qty","Unit","Price","Total","Paid","Change","Receipt","Payment","Attendant","Recorded By","Pump"])
    for s in data.sales:
        writer.writerow([
            s.sold_at.strftime("%Y-%m-%d"),
            s.sold_at.strftime("%H:%M:%S"),
            s.product_type.value,
            s.product_name,
            f"{s.quantity:.2f}",
            s.unit,
            f"{s.price_per_unit:.2f}",
            f"{s.total_amount:.2f}",
            f"{s.amount_paid:.2f}",
            f"{s.change_given:.2f}",
            s.receipt_no or "",
            s.payment_method,
            s.attendant_name,
            s.recorded_by,
            s.pump_name or ""
        ])
    output.seek(0)
    filename = f"unified_sales_{start_date or 'all'}_to_{end_date or 'all'}.csv"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})