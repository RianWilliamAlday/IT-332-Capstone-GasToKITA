from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from..db.database import get_session, Attendant, Sale, OilSale
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/attendants", tags=["Attendants"])

class AttendantCreate(BaseModel):
    name: str
    employee_id: Optional[str] = None
    contact: Optional[str] = None

class AttendantUpdate(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/")
def add_attendant(data: AttendantCreate, session: Session = Depends(get_session)):
    clean = data.name.strip()
    if session.exec(select(Attendant).where(func.lower(Attendant.name) == clean.lower())).first():
        raise HTTPException(400, f"'{clean}' already exists")
    att = Attendant(name=clean, employee_id=data.employee_id, contact=data.contact, is_active=True,
                    created_at=datetime.now(), updated_at=datetime.now())
    session.add(att); session.commit(); session.refresh(att)
    return att

@router.get("/")
def list_attendants(include_inactive: bool = False, search: str = None, session: Session = Depends(get_session)):
    q = select(Attendant)
    if not include_inactive: q = q.where(Attendant.is_active == True)
    if search: q = q.where(Attendant.name.ilike(f"%{search}%"))
    return session.exec(q.order_by(Attendant.name)).all()

@router.get("/active")
def list_active(session: Session = Depends(get_session)):
    return session.exec(select(Attendant).where(Attendant.is_active == True).order_by(Attendant.name)).all()

@router.get("/names")
def list_names(session: Session = Depends(get_session)):
    names = session.exec(select(Attendant.name).where(Attendant.is_active == True).order_by(Attendant.name)).all()
    return names if names else ["Attendant 1","Attendant 2","Attendant 3"]

@router.put("/{attendant_id}")
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

@router.patch("/{attendant_id}/rename")
def rename_attendant(attendant_id: int, new_name: str = Query(...), session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    if not att: raise HTTPException(404, "Not found")
    clean = new_name.strip()
    if session.exec(select(Attendant).where(func.lower(Attendant.name) == clean.lower(), Attendant.id!= attendant_id)).first():
        raise HTTPException(400, "Name exists")
    att.name = clean; att.updated_at = datetime.now()
    session.add(att); session.commit(); session.refresh(att)
    return att

@router.patch("/{attendant_id}/deactivate")
def deactivate(attendant_id: int, session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    att.is_active = False; att.deactivated_at = datetime.now(); att.updated_at = datetime.now()
    session.add(att); session.commit()
    return {"message": f"{att.name} deactivated"}

@router.delete("/{attendant_id}")
def remove(attendant_id: int, force: bool = False, session: Session = Depends(get_session)):
    att = session.get(Attendant, attendant_id)
    cnt = session.exec(select(func.count()).select_from(Sale).where(Sale.attendant_name == att.name)).one()
    if cnt > 0 and not force:
        raise HTTPException(400, f"Has {cnt} sales - deactivate or use?force=true")
    session.delete(att); session.commit()
    return {"message": f"{att.name} removed"}

@router.post("/seed-defaults")
def seed(session: Session = Depends(get_session)):
    if session.exec(select(Attendant)).first(): return {"message": "already seeded"}
    for n in ["Attendant 1","Attendant 2","Attendant 3"]:
        session.add(Attendant(name=n, display_name=n, is_active=True, created_at=datetime.now(), updated_at=datetime.now()))
    session.commit()
    return {"message": "seeded"}