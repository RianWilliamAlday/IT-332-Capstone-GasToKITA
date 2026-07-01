from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional

engine = create_engine("sqlite:///gastokita.db", echo=True) # echo=True shows SQL in logs

class Fuel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    actual_liters: float
    tank_capacity: float # <-- add this

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