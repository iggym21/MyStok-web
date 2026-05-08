import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, SessionLocal
from backend.models import Base
from backend.importer import import_stocks
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routers import health, sectors, stocks, recommend

logging.basicConfig(level=logging.INFO)
CSV_PATH = os.getenv("MYSTOK_CSV_PATH", "data/kaggle_stocks.csv")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.path.exists(CSV_PATH):
        db = SessionLocal()
        try:
            import_stocks(CSV_PATH, db)
        finally:
            db.close()
    else:
        logging.warning("CSV not found at %s — skipping import", CSV_PATH)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="MyStok API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sectors.router)
app.include_router(stocks.router)
app.include_router(recommend.router)
