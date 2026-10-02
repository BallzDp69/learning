from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=1, max_length=120)


class UserRead(ORMModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    price_cents: int = Field(ge=0)
    initial_quantity: int = Field(default=0, ge=0)


class ProductRead(ORMModel):
    id: int
    sku: str
    name: str
    description: str
    price_cents: int
    is_active: bool


class InventoryRead(BaseModel):
    product_id: int
    quantity: int


class InventoryAdjust(BaseModel):
    delta: int

    @field_validator("delta")
    @classmethod
    def delta_must_not_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("delta must not be zero")
        return value


class DiscountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    percent_off: int = Field(ge=1, le=100)
    minimum_subtotal_cents: int = Field(default=0, ge=0)
    expires_at: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)


class DiscountRead(ORMModel):
    id: int
    code: str
    percent_off: int
    minimum_subtotal_cents: int
    active: bool
    expires_at: datetime | None
    max_uses: int | None
    times_used: int


class CartCreate(BaseModel):
    user_id: int


class CartItemWrite(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=1000)


class ApplyDiscount(BaseModel):
    code: str


class CartItemRead(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class CartRead(BaseModel):
    id: int
    user_id: int
    status: str
    discount_code: str | None
    items: list[CartItemRead]
    subtotal_cents: int
    discount_cents: int
    total_cents: int


class CheckoutRequest(BaseModel):
    payment_token: str = Field(min_length=1, max_length=100)


class OrderItemRead(ORMModel):
    product_id: int
    sku: str
    product_name: str
    unit_price_cents: int
    quantity: int


class OrderRead(ORMModel):
    id: int
    order_number: str
    user_id: int
    status: str
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    created_at: datetime
    items: list[OrderItemRead]


class RefundCreate(BaseModel):
    amount_cents: int = Field(gt=0)
    reason: str = Field(min_length=3, max_length=300)


class RefundRead(ORMModel):
    id: int
    order_id: int
    amount_cents: int
    reason: str
    reference: str
    created_at: datetime


class SalesReport(BaseModel):
    order_count: int
    gross_sales_cents: int
    discounts_cents: int
    refunds_cents: int
    net_sales_cents: int
