from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import DiscountCreate, DiscountRead
from ..services.discounts import create_discount

router = APIRouter(prefix="/discounts", tags=["discounts"])


@router.post("", response_model=DiscountRead, status_code=201)
def create(data: DiscountCreate, session: Session = Depends(get_session)):
    return create_discount(session, data)
