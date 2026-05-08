from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Fundamentals
from backend.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    last = db.query(func.max(Fundamentals.last_updated)).scalar()
    return HealthResponse(status="ok", last_refresh=last)
