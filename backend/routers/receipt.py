from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
from ..db.database import get_session, Sale, OilSale

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

def build_pdf_bytes(sale, sale_type):
    buf = io.BytesIO()
    w, h = 80*mm, 200*mm
    c = canvas.Canvas(buf, pagesize=(w,h))
    y = h - 10*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w/2, y, "U-FUEL")
    y-=5*mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(w/2, y, f"Receipt: {sale.receipt_no or sale.id}")
    y-=4*mm
    c.drawCentredString(w/2, y, f"{sale.sold_at:%Y-%m-%d %H:%M}")
    y-=6*mm
    c.line(5*mm,y,w-5*mm,y); y-=6*mm
    c.setFont("Helvetica", 8)

    if sale_type == "fuel":
        c.drawString(5*mm,y,f"{sale.liters_sold}L x P{sale.price_per_liter:.2f}"); y-=5*mm
    else:
        c.drawString(5*mm,y,f"Oil x{sale.quantity} @ P{sale.price_per_unit:.2f}"); y-=5*mm

    c.drawString(5*mm,y,f"Due: P{sale.total_amount:.2f}"); y-=5*mm
    c.drawString(5*mm,y,f"Paid: P{sale.amount_paid:.2f}"); y-=5*mm
    c.setFont("Helvetica-Bold",9)
    c.drawString(5*mm,y,f"CHANGE: P{sale.change_given:.2f}")
    c.showPage(); c.save(); buf.seek(0)
    return buf

@router.get("/{sale_type}/{sale_id}/pdf")
def get_receipt_pdf(sale_type: str, sale_id: int, session: Session = Depends(get_session)):
    if sale_type == "fuel":
        sale = session.get(Sale, sale_id)
    else:
        sale = session.get(OilSale, sale_id)
    if not sale:
        raise HTTPException(404, "Sale not found")
    pdf = build_pdf_bytes(sale, sale_type)
    return StreamingResponse(pdf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=receipt_{sale_type}_{sale_id}.pdf"})