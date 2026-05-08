from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Stock

router = APIRouter()

@router.get("/sectors", response_model=list[str])
def sectors(db: Session = Depends(get_db)):
    rows = (
        db.query(Stock.sector)
        .filter(Stock.sector.isnot(None))
        .distinct()
        .order_by(Stock.sector)
        .all()
    )
    return [r.sector for r in rows]
