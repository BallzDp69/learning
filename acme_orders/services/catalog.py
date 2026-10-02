from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import Inventory, Product, User
from ..schemas import ProductCreate, UserCreate


def create_user(session: Session, data: UserCreate) -> User:
    user = User(email=data.email.strip().lower(), full_name=data.full_name.strip())
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("a user with that email already exists") from None
    session.refresh(user)
    return user


def get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError("user not found")
    return user


def create_product(session: Session, data: ProductCreate) -> Product:
    product = Product(
        sku=data.sku.strip().upper(),
        name=data.name.strip(),
        description=data.description.strip(),
        price_cents=data.price_cents,
    )
    product.inventory = Inventory(quantity=data.initial_quantity)
    session.add(product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("a product with that SKU already exists") from None
    session.refresh(product)
    return product


def list_products(session: Session, *, active_only: bool = True) -> list[Product]:
    query = select(Product).order_by(Product.name)
    if active_only:
        query = query.where(Product.is_active.is_(True))
    return list(session.scalars(query))


def get_product(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("product not found")
    return product


def adjust_inventory(session: Session, product_id: int, delta: int) -> Inventory:
    product = get_product(session, product_id)
    inventory = product.inventory
    if inventory.quantity + delta < 0:
        raise ConflictError("inventory cannot become negative")
    inventory.quantity += delta
    session.commit()
    session.refresh(inventory)
    return inventory
