from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import fuels, pumps, dispense
from db.database import create_db_and_tables

app = FastAPI(
    title="U-Fuel Backend",
    description="API for gas station app",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fuels.router)
app.include_router(pumps.router)
app.include_router(dispense.router)

@app.get("/")
def read_root():
    """Redirects the root URL to the interactive API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()