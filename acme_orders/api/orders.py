from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import CheckoutRequest, OrderRead, RefundCreate, RefundRead
from ..services import orders

router = APIRouter(tags=["orders"])


@router.post("/carts/{cart_id}/checkout", response_model=OrderRead, status_code=201)
def checkout(cart_id: int, data: CheckoutRequest, session: Session = Depends(get_session)):
    return orders.checkout(session, cart_id, data.payment_token)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get(order_id: int, session: Session = Depends(get_session)):
    return orders.get_order(session, order_id)


@router.post("/orders/{order_id}/refunds", response_model=RefundRead, status_code=201)
def refund(order_id: int, data: RefundCreate, session: Session = Depends(get_session)):
    return orders.issue_refund(session, order_id, data.amount_cents, data.reason)
