# AcmeOrders

AcmeOrders is a compact but production-shaped FastAPI backend for a small online
shop. It manages customers, catalog products, stock, carts, checkout, discounts,
local payment simulation, refunds, and sales reporting.

## Architecture

The application uses a conventional layered layout:

- `acme_orders/api/` contains HTTP routers and dependency wiring.
- `acme_orders/models.py` contains SQLAlchemy persistence models.
- `acme_orders/schemas.py` defines request and response contracts.
- `acme_orders/services/` owns business workflows and transaction boundaries.
- `acme_orders/db.py` configures engines, sessions, and schema initialization.
- `scripts/seed.py` creates a useful local catalog and demo account.
- `tests/` exercises service rules and end-to-end API behavior.

Amounts are stored as integer cents. Timestamps are UTC. Payment processing is a
deterministic local simulator; no external payment provider is contacted.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Initialize and seed a development database:

```bash
python -m scripts.seed
```

Start the API:

```bash
uvicorn acme_orders.main:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Testing

```bash
pytest
```

Tests use a temporary SQLite database and never modify the development database.

## Main API workflows

1. Create a user and products, then adjust product inventory.
2. Create a cart for a user and add active, in-stock products.
3. Apply an eligible discount code and preview cart totals.
4. Checkout using a local payment token such as `tok_success`.
5. Inspect the order or issue a full/partial refund.
6. Query `/reports/sales` for aggregate sales and refund metrics.

The simulator also accepts `tok_declined`; checkout records a declined payment
without creating an order or consuming inventory.
