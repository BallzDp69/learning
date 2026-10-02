from datetime import datetime, timedelta, timezone

from acme_orders.models import Product


def make_cart(client, user_payload, product_payload):
    user_id = client.post("/users", json=user_payload).json()["id"]
    product_id = client.post("/products", json=product_payload).json()["id"]
    cart_id = client.post("/carts", json={"user_id": user_id}).json()["id"]
    return cart_id, product_id


def test_create_empty_cart(client, user_payload):
    user_id = client.post("/users", json=user_payload).json()["id"]
    response = client.post("/carts", json={"user_id": user_id})
    assert response.status_code == 201
    assert response.json()["items"] == []
    assert response.json()["total_cents"] == 0


def test_add_same_item_accumulates_quantity(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    assert client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 2}).status_code == 200
    response = client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 3})
    assert response.json()["items"][0]["quantity"] == 5
    assert response.json()["subtotal_cents"] == 12500


def test_cannot_add_more_than_inventory(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    response = client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 11})
    assert response.status_code == 409


def test_update_and_remove_item(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 2})
    updated = client.put(f"/carts/{cart_id}/items/{product_id}", json={"product_id": product_id, "quantity": 4})
    assert updated.json()["items"][0]["quantity"] == 4
    removed = client.delete(f"/carts/{cart_id}/items/{product_id}")
    assert removed.status_code == 204
    assert client.get(f"/carts/{cart_id}").json()["items"] == []


def test_inactive_product_cannot_be_added(client, session, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    session.get(Product, product_id).is_active = False
    session.commit()
    response = client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
    assert response.status_code == 409


def test_apply_percentage_discount(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 2})
    discount = {"code": "SAVE20", "percent_off": 20, "minimum_subtotal_cents": 4000}
    assert client.post("/discounts", json=discount).status_code == 201
    response = client.post(f"/carts/{cart_id}/discount", json={"code": "save20"})
    assert response.status_code == 200
    assert response.json()["discount_cents"] == 1000
    assert response.json()["total_cents"] == 4000


def test_discount_minimum_is_enforced(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
    client.post("/discounts", json={"code": "BIG", "percent_off": 10, "minimum_subtotal_cents": 5000})
    response = client.post(f"/carts/{cart_id}/discount", json={"code": "BIG"})
    assert response.status_code == 409


def test_expired_discount_is_rejected(client, user_payload, product_payload):
    cart_id, product_id = make_cart(client, user_payload, product_payload)
    client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client.post("/discounts", json={"code": "OLD", "percent_off": 5, "expires_at": expired})
    response = client.post(f"/carts/{cart_id}/discount", json={"code": "OLD"})
    assert response.status_code == 409
