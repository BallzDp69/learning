from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from ..errors import ConflictError, NotFoundError
from ..models import Cart, CartItem, CartStatus, Product
from ..schemas import CartRead, CartItemRead
from .catalog import get_product, get_user
from .discounts import discount_amount, get_discount_by_code, validate_discount


def create_cart(session: Session, user_id: int) -> Cart:
    user = get_user(session, user_id)
    if not user.is_active:
        raise ConflictError("inactive users cannot create carts")
    cart = Cart(user_id=user_id)
    session.add(cart)
    session.commit()
    session.refresh(cart)
    return cart


def get_cart(session: Session, cart_id: int) -> Cart:
    query = (
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product), selectinload(Cart.discount))
    )
    cart = session.scalar(query)
    if cart is None:
        raise NotFoundError("cart not found")
    return cart


def require_open(cart: Cart) -> None:
    if cart.status != CartStatus.OPEN.value:
        raise ConflictError("cart is not open")


def add_item(session: Session, cart_id: int, product_id: int, quantity: int) -> Cart:
    cart = get_cart(session, cart_id)
    require_open(cart)
    product = get_product(session, product_id)
    if not product.is_active:
        raise ConflictError("product is inactive")
    existing = next((item for item in cart.items if item.product_id == product_id), None)
    desired_quantity = quantity
    if product.inventory.quantity < desired_quantity:
        raise ConflictError("insufficient inventory")
    if existing:
        existing.quantity = desired_quantity
    else:
        session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
    session.commit()
    return get_cart(session, cart_id)


def update_item(session: Session, cart_id: int, product_id: int, quantity: int) -> Cart:
    cart = get_cart(session, cart_id)
    require_open(cart)
    item = next((item for item in cart.items if item.product_id == product_id), None)
    if item is None:
        raise NotFoundError("cart item not found")
    product = get_product(session, product_id)
    if product.inventory.quantity < quantity:
        raise ConflictError("insufficient inventory")
    item.quantity = quantity
    session.commit()
    return get_cart(session, cart_id)


def remove_item(session: Session, cart_id: int, product_id: int) -> Cart:
    cart = get_cart(session, cart_id)
    require_open(cart)
    item = next((item for item in cart.items if item.product_id == product_id), None)
    if item is None:
        raise NotFoundError("cart item not found")
    session.delete(item)
    session.commit()
    session.expire_all()
    return get_cart(session, cart_id)


def subtotal(cart: Cart) -> int:
    return sum(item.product.price_cents * item.quantity for item in cart.items)


def apply_discount(session: Session, cart_id: int, code: str) -> Cart:
    cart = get_cart(session, cart_id)
    require_open(cart)
    discount = get_discount_by_code(session, code)
    validate_discount(discount, subtotal(cart))
    cart.discount = discount
    session.commit()
    return get_cart(session, cart_id)


def serialize_cart(cart: Cart) -> CartRead:
    subtotal_cents = subtotal(cart)
    discount_cents = 0
    if cart.discount:
        try:
            validate_discount(cart.discount, subtotal_cents)
            discount_cents = discount_amount(subtotal_cents, cart.discount.percent_off)
        except ConflictError:
            discount_cents = 0
    return CartRead(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status,
        discount_code=cart.discount.code if cart.discount else None,
        items=[
            CartItemRead(
                product_id=item.product_id,
                sku=item.product.sku,
                name=item.product.name,
                unit_price_cents=item.product.price_cents,
                quantity=item.quantity,
                line_total_cents=item.product.price_cents * item.quantity,
            )
            for item in cart.items
        ],
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=subtotal_cents - discount_cents,
    )
