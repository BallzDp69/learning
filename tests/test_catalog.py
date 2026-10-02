from acme_orders.models import Inventory, Product


def test_create_and_get_user(client, user_payload):
    created = client.post("/users", json=user_payload)
    assert created.status_code == 201
    assert created.json()["email"] == "buyer@example.test"
    fetched = client.get(f"/users/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["full_name"] == "Casey Buyer"


def test_email_is_unique_ignoring_case(client, user_payload):
    assert client.post("/users", json=user_payload).status_code == 201
    duplicate = {**user_payload, "email": "BUYER@example.test"}
    response = client.post("/users", json=duplicate)
    assert response.status_code == 409


def test_invalid_email_is_rejected(client):
    response = client.post("/users", json={"email": "nope", "full_name": "Someone"})
    assert response.status_code == 422


def test_product_creation_normalizes_sku_and_creates_inventory(client, session, product_payload):
    product_payload["sku"] = " widget-1 "
    response = client.post("/products", json=product_payload)
    assert response.status_code == 201
    assert response.json()["sku"] == "WIDGET-1"
    product = session.get(Product, response.json()["id"])
    assert product.inventory.quantity == 10


def test_duplicate_sku_returns_conflict(client, product_payload):
    assert client.post("/products", json=product_payload).status_code == 201
    assert client.post("/products", json=product_payload).status_code == 409


def test_list_products_hides_inactive_by_default(client, session, product_payload):
    product_id = client.post("/products", json=product_payload).json()["id"]
    product = session.get(Product, product_id)
    product.is_active = False
    session.commit()
    assert client.get("/products").json() == []
    assert len(client.get("/products?include_inactive=true").json()) == 1


def test_adjust_inventory(client, product_payload):
    product_id = client.post("/products", json=product_payload).json()["id"]
    response = client.patch(f"/products/{product_id}/inventory", json={"delta": -3})
    assert response.status_code == 200
    assert response.json() == {"product_id": product_id, "quantity": 7}


def test_inventory_cannot_be_negative(client, product_payload):
    product_id = client.post("/products", json=product_payload).json()["id"]
    response = client.patch(f"/products/{product_id}/inventory", json={"delta": -11})
    assert response.status_code == 409
    assert "negative" in response.json()["detail"]


def test_inventory_delta_cannot_be_zero(client, product_payload):
    product_id = client.post("/products", json=product_payload).json()["id"]
    assert client.patch(f"/products/{product_id}/inventory", json={"delta": 0}).status_code == 422
