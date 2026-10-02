from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas import InventoryAdjust, InventoryRead, ProductCreate, ProductRead, UserCreate, UserRead
from ..services import catalog

router = APIRouter(tags=["catalog"])


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    return catalog.create_user(session, data)


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    return catalog.get_user(session, user_id)


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(data: ProductCreate, session: Session = Depends(get_session)):
    return catalog.create_product(session, data)


@router.get("/products", response_model=list[ProductRead])
def list_products(include_inactive: bool = Query(False), session: Session = Depends(get_session)):
    return catalog.list_products(session, active_only=not include_inactive)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    return catalog.get_product(session, product_id)


@router.patch("/products/{product_id}/inventory", response_model=InventoryRead)
def adjust_inventory(product_id: int, data: InventoryAdjust, session: Session = Depends(get_session)):
    return catalog.adjust_inventory(session, product_id, data.delta)
