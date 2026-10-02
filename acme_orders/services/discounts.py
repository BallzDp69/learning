from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import ConflictError, NotFoundError
from ..models import Discount
from ..schemas import DiscountCreate


def create_discount(session: Session, data: DiscountCreate) -> Discount:
    discount = Discount(code=data.code.strip().upper(), **data.model_dump(exclude={"code"}))
    session.add(discount)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("discount code already exists") from None
    session.refresh(discount)
    return discount


def validate_discount(discount: Discount, subtotal_cents: int) -> None:
    now = datetime.now(timezone.utc)
    expires_at = discount.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not discount.active:
        raise ConflictError("discount is inactive")
    if expires_at is not None and expires_at <= now:
        raise ConflictError("discount has expired")
    if discount.max_uses is not None and discount.times_used >= discount.max_uses:
        raise ConflictError("discount usage limit reached")
    if subtotal_cents < discount.minimum_subtotal_cents:
        raise ConflictError("cart does not meet discount minimum")


def get_discount_by_code(session: Session, code: str) -> Discount:
    discount = session.query(Discount).filter(Discount.code == code.strip().upper()).one_or_none()
    if discount is None:
        raise NotFoundError("discount code not found")
    return discount


def discount_amount(subtotal_cents: int, percent_off: int) -> int:
    return subtotal_cents * percent_off // 100
