from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_FILE = PROJECT_ROOT / "gastokita.db"
engine = create_engine("sqlite:///gastokita.db", echo=False)
print(f"=== USING DATABASE: {DB_FILE} ===")

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    password_hash: str
    role: UserRole
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Fuel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    actual_liters: float
    tank_capacity: float

class Pump(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    fuel_type_id: int = Field(foreign_key="fuel.id")
    status: str = "Available"

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session