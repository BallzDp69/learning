from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from acme_orders.db import SessionLocal, init_db
from acme_orders.models import Product, User
from acme_orders.schemas import DiscountCreate, ProductCreate, UserCreate
from acme_orders.services.catalog import create_product, create_user
from acme_orders.services.discounts import create_discount


def seed() -> None:
    init_db()
    with SessionLocal() as session:
        if session.scalar(select(func.count(User.id))):
            print("Database already contains data; nothing seeded.")
            return
        create_user(session, UserCreate(email="demo@acme.test", full_name="Demo Customer"))
        products = [
            ProductCreate(sku="MUG-BLUE", name="Blue Acme Mug", price_cents=1299, initial_quantity=40,
                          description="A sturdy ceramic mug."),
            ProductCreate(sku="TEE-BASIC", name="Acme Logo T-Shirt", price_cents=2499, initial_quantity=25,
                          description="Cotton shirt in unisex sizing."),
            ProductCreate(sku="NOTE-A5", name="A5 Notebook", price_cents=899, initial_quantity=100,
                          description="Hardcover dotted notebook."),
        ]
        for product in products:
            create_product(session, product)
        create_discount(session, DiscountCreate(
            code="WELCOME10", percent_off=10, minimum_subtotal_cents=1000,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365), max_uses=500,
        ))
        count = session.scalar(select(func.count(Product.id)))
        print(f"Seeded demo user, {count} products, and WELCOME10 discount.")


if __name__ == "__main__":
    seed()
