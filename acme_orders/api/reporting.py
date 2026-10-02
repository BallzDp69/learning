from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import SalesReport
from ..services.reporting import sales_report

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get("/sales", response_model=SalesReport)
def sales(start: datetime | None = Query(None), end: datetime | None = Query(None),
          session: Session = Depends(get_session)):
    return sales_report(session, start, end)
