from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import ApplyDiscount, CartCreate, CartItemWrite, CartRead
from ..services import carts

router = APIRouter(prefix="/carts", tags=["carts"])


@router.post("", response_model=CartRead, status_code=201)
def create(data: CartCreate, session: Session = Depends(get_session)):
    cart = carts.create_cart(session, data.user_id)
    return carts.serialize_cart(carts.get_cart(session, cart.id))


@router.get("/{cart_id}", response_model=CartRead)
def get(cart_id: int, session: Session = Depends(get_session)):
    return carts.serialize_cart(carts.get_cart(session, cart_id))


@router.post("/{cart_id}/items", response_model=CartRead)
def add_item(cart_id: int, data: CartItemWrite, session: Session = Depends(get_session)):
    return carts.serialize_cart(carts.add_item(session, cart_id, data.product_id, data.quantity))


@router.put("/{cart_id}/items/{product_id}", response_model=CartRead)
def update_item(cart_id: int, product_id: int, data: CartItemWrite, session: Session = Depends(get_session)):
    if data.product_id != product_id:
        from ..errors import ConflictError
        raise ConflictError("product IDs do not match")
    return carts.serialize_cart(carts.update_item(session, cart_id, product_id, data.quantity))


@router.delete("/{cart_id}/items/{product_id}", status_code=204)
def remove_item(cart_id: int, product_id: int, session: Session = Depends(get_session)):
    carts.remove_item(session, cart_id, product_id)
    return Response(status_code=204)


@router.post("/{cart_id}/discount", response_model=CartRead)
def apply_discount(cart_id: int, data: ApplyDiscount, session: Session = Depends(get_session)):
    return carts.serialize_cart(carts.apply_discount(session, cart_id, data.code))
