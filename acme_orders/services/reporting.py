from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Order, Refund
from ..schemas import SalesReport


def sales_report(session: Session, start: datetime | None = None, end: datetime | None = None) -> SalesReport:
    order_filters = []
    refund_filters = []
    if start:
        order_filters.append(Order.created_at >= start)
        refund_filters.append(Refund.created_at >= start)
    if end:
        order_filters.append(Order.created_at < end)
        refund_filters.append(Refund.created_at < end)
    count, gross, discounts = session.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.subtotal_cents), 0),
               func.coalesce(func.sum(Order.discount_cents), 0)).where(*order_filters)
    ).one()
    refunds = session.scalar(select(func.coalesce(func.sum(Refund.amount_cents), 0)).where(*refund_filters))
    net = int(gross) - int(discounts) - int(refunds)
    return SalesReport(order_count=count, gross_sales_cents=gross, discounts_cents=discounts,
                       refunds_cents=refunds, net_sales_cents=net)
