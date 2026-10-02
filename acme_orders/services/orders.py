from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..errors import ConflictError, NotFoundError, PaymentDeclinedError
from ..models import (
    CartStatus, Order, OrderItem, OrderStatus, Payment, PaymentStatus, Refund,
)
from . import payments
from .carts import get_cart, require_open, subtotal
from .discounts import discount_amount, validate_discount


def get_order(session: Session, order_id: int) -> Order:
    query = select(Order).where(Order.id == order_id).options(
        selectinload(Order.items), selectinload(Order.payment), selectinload(Order.refunds)
    )
    order = session.scalar(query)
    if order is None:
        raise NotFoundError("order not found")
    return order


def checkout(session: Session, cart_id: int, payment_token: str) -> Order:
    cart = get_cart(session, cart_id)
    require_open(cart)
    if not cart.items:
        raise ConflictError("cannot checkout an empty cart")

    subtotal_cents = subtotal(cart)
    discount_cents = 0
    if cart.discount:
        validate_discount(cart.discount, subtotal_cents)
        discount_cents = discount_amount(subtotal_cents, cart.discount.percent_off)
    total_cents = subtotal_cents - discount_cents

    for item in cart.items:
        if not item.product.is_active:
            raise ConflictError(f"product {item.product.sku} is inactive")
        if item.product.inventory.quantity < item.quantity:
            raise ConflictError(f"insufficient inventory for {item.product.sku}")

    result = payments.capture(payment_token, total_cents)
    if not result.accepted:
        session.add(Payment(
            cart_id=cart.id, provider_reference=result.reference,
            amount_cents=total_cents, status=PaymentStatus.DECLINED.value,
        ))
        session.commit()
        raise PaymentDeclinedError(result.message)

    order = Order(
        order_number=f"ACME-{uuid4().hex[:12].upper()}",
        user_id=cart.user_id,
        cart_id=cart.id,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
    )
    for item in cart.items:
        item.product.inventory.quantity -= item.quantity
        order.items.append(OrderItem(
            product_id=item.product_id,
            sku=item.product.sku,
            product_name=item.product.name,
            unit_price_cents=item.product.price_cents,
            quantity=item.quantity,
        ))
    order.payment = Payment(
        cart_id=cart.id, provider_reference=result.reference,
        amount_cents=total_cents, status=PaymentStatus.CAPTURED.value,
    )
    cart.status = CartStatus.CHECKED_OUT.value
    if cart.discount:
        cart.discount.times_used += 1
    session.add(order)
    session.commit()
    return get_order(session, order.id)


def issue_refund(session: Session, order_id: int, amount_cents: int, reason: str) -> Refund:
    order = get_order(session, order_id)
    refundable = order.total_cents - order.payment.refunded_cents
    if amount_cents > refundable:
        raise ConflictError("refund exceeds remaining refundable amount")
    reference = payments.refund(order.payment.provider_reference, amount_cents)
    refund = Refund(order_id=order.id, amount_cents=amount_cents, reason=reason, reference=reference)
    order.payment.refunded_cents += amount_cents
    if order.payment.refunded_cents == order.total_cents:
        order.payment.status = PaymentStatus.REFUNDED.value
        order.status = OrderStatus.REFUNDED.value
    else:
        order.payment.status = PaymentStatus.PARTIALLY_REFUNDED.value
        order.status = OrderStatus.PARTIALLY_REFUNDED.value
    session.add(refund)
    session.commit()
    session.refresh(refund)
    return refund
