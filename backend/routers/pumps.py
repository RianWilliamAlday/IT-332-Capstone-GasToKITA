from fastapi import APIRouter
from typing import List
from models.schemas import Pump
from db.data import pumps

router = APIRouter(prefix="/api/pumps", tags=["pumps"])

@router.get("", response_model=List[Pump])
def get_pumps():
    """Return all pumps with their current status"""
    return pumps