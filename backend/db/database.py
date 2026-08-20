from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_FILE = PROJECT_ROOT / "gastokita.db"
engine = create_engine("sqlite:///gastokita.db", echo=False)

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
    threshold: float = Field(default=100.0)
    last_restocked: Optional[datetime] = Field(default=None)

class Pump(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    fuel_type_id: int = Field(foreign_key="fuel.id")
    status: str = "Available"


class FuelBatch(SQLModel, table=True):
    __tablename__ = "fuel_batch"
    id: Optional[int] = Field(default=None, primary_key=True)
    fuel_id: int = Field(foreign_key="fuel.id", index=True)
    liters_initial: float
    liters_remaining: float
    cost_per_liter: float
    selling_price: float
    supplier: Optional[str] = None
    restocked_by: Optional[str] = None
    restocked_at: datetime = Field(default_factory=datetime.now)

class FuelSaleBatch(SQLModel, table=True):
    __tablename__ = "fuel_sale_batch"
    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sale.id", index=True)
    batch_id: int = Field(foreign_key="fuel_batch.id", index=True)
    liters_consumed: float
    price_per_liter: float
    total_amount: float
    consumed_at: datetime = Field(default_factory=datetime.now)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

class RestockLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fuel_id: int = Field(foreign_key="fuel.id")
    liters_added: float
    cost: float
    supplier: Optional[str] = None
    restocked_by: str
    restocked_at: datetime = Field(default_factory=datetime.now)

class Sale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fuel_id: int = Field(foreign_key="fuel.id")
    pump_id: int = Field(foreign_key="pump.id")
    attendant_name: str = Field(index=True)
    recorded_by: int = Field(foreign_key="user.id")
    liters_sold: float
    price_per_liter: float
    total_amount: float
    amount_paid: float = Field(default=0)
    change_given: float = Field(default=0)
    receipt_no: Optional[str] = Field(default=None, index=True)
    payment_method: str = Field(default="cash")
    sold_at: datetime = Field(default_factory=datetime.now)
    recorded_by_user: Optional[User] = Relationship()
    fuel: Optional[Fuel] = Relationship()

class OilProduct(SQLModel, table=True):
    __tablename__ = "oil_product"
    id: Optional[int] = Field(default=None, primary_key=True)
    brand: str = Field(index=True)
    name: str = Field(index=True)
    variant: Optional[str] = None
    stock: int = Field(default=0)
    price: float
    cost: float = Field(default=0)
    low_stock_threshold: int = Field(default=5)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class OilRestockLog(SQLModel, table=True):
    __tablename__ = "oil_restock_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    oil_product_id: int = Field(foreign_key="oil_product.id")
    quantity_added: int
    total_cost: float
    supplier: Optional[str] = None
    restocked_by: Optional[int] = Field(default=None, foreign_key="user.id")
    restocked_at: datetime = Field(default_factory=datetime.now)

class OilSale(SQLModel, table=True):
    __tablename__ = "oil_sale"
    id: Optional[int] = Field(default=None, primary_key=True)
    oil_product_id: int = Field(foreign_key="oil_product.id")
    quantity: int
    price_per_unit: float
    total_amount: float
    amount_paid: float = Field(default=0)
    change_given: float = Field(default=0)
    receipt_no: Optional[str] = Field(default=None, index=True)
    payment_method: str = Field(default="cash")
    sold_at: datetime = Field(default_factory=datetime.now)
    sold_by: Optional[int] = Field(default=None, foreign_key="user.id")
    attendant_name: Optional[str] = None

class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True)
    description: Optional[str] = None
    amount: float
    expense_date: datetime = Field(default_factory=datetime.now)
    recorded_by: Optional[int] = Field(default=None, foreign_key="user.id")

class Attendant(SQLModel, table=True):
    __tablename__ = "attendant"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    employee_id: Optional[str] = Field(default=None, index=True)
    contact: Optional[str] = Field(default=None, description="Email OR phone number")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deactivated_at: Optional[datetime] = None