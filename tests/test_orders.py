from acme_orders.models import Cart, Inventory, Payment, Refund


def setup_cart(client, user_payload, product_payload, quantity=2):
    user_id = client.post("/users", json=user_payload).json()["id"]
    product_id = client.post("/products", json=product_payload).json()["id"]
    cart_id = client.post("/carts", json={"user_id": user_id}).json()["id"]
    client.post(f"/carts/{cart_id}/items", json={"product_id": product_id, "quantity": quantity})
    return cart_id, product_id


def test_checkout_creates_snapshot_and_reduces_inventory(client, session, user_payload, product_payload):
    cart_id, product_id = setup_cart(client, user_payload, product_payload)
    response = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "paid"
    assert body["total_cents"] == 5000
    assert body["items"][0]["product_name"] == "Useful Widget"
    assert session.get(Inventory, product_id).quantity == 8
    assert session.get(Cart, cart_id).status == "checked_out"


def test_empty_cart_cannot_checkout(client, user_payload):
    user_id = client.post("/users", json=user_payload).json()["id"]
    cart_id = client.post("/carts", json={"user_id": user_id}).json()["id"]
    response = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"})
    assert response.status_code == 409


def test_declined_payment_preserves_cart_and_inventory(client, session, user_payload, product_payload):
    cart_id, product_id = setup_cart(client, user_payload, product_payload)
    response = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_declined"})
    assert response.status_code == 402
    assert session.get(Cart, cart_id).status == "open"
    assert session.get(Inventory, product_id).quantity == 10
    payment = session.query(Payment).one()
    assert payment.status == "declined"
    assert payment.order_id is None


def test_cart_cannot_checkout_twice(client, user_payload, product_payload):
    cart_id, _ = setup_cart(client, user_payload, product_payload)
    assert client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"}).status_code == 201
    assert client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"}).status_code == 409


def test_checkout_increments_discount_usage(client, user_payload, product_payload):
    cart_id, _ = setup_cart(client, user_payload, product_payload)
    discount_id = client.post("/discounts", json={"code": "ONCE", "percent_off": 10, "max_uses": 1}).json()["id"]
    client.post(f"/carts/{cart_id}/discount", json={"code": "ONCE"})
    response = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"})
    assert response.status_code == 201
    assert response.json()["discount_cents"] == 500


def test_partial_then_full_refund(client, session, user_payload, product_payload):
    cart_id, _ = setup_cart(client, user_payload, product_payload)
    order = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"}).json()
    first = client.post(f"/orders/{order['id']}/refunds", json={"amount_cents": 1200, "reason": "Returned one item"})
    assert first.status_code == 201
    assert client.get(f"/orders/{order['id']}").json()["status"] == "partially_refunded"
    second = client.post(f"/orders/{order['id']}/refunds", json={"amount_cents": 3800, "reason": "Returned remainder"})
    assert second.status_code == 201
    assert client.get(f"/orders/{order['id']}").json()["status"] == "refunded"
    assert session.query(Refund).count() == 2


def test_refund_cannot_exceed_total(client, user_payload, product_payload):
    cart_id, _ = setup_cart(client, user_payload, product_payload)
    order = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"}).json()
    response = client.post(f"/orders/{order['id']}/refunds", json={"amount_cents": 5001, "reason": "Too much"})
    assert response.status_code == 409


def test_sales_report_accounts_for_discount_and_refund(client, user_payload, product_payload):
    cart_id, _ = setup_cart(client, user_payload, product_payload)
    client.post("/discounts", json={"code": "TEN", "percent_off": 10})
    client.post(f"/carts/{cart_id}/discount", json={"code": "TEN"})
    order = client.post(f"/carts/{cart_id}/checkout", json={"payment_token": "tok_success"}).json()
    client.post(f"/orders/{order['id']}/refunds", json={"amount_cents": 1000, "reason": "Damaged box"})
    report = client.get("/reports/sales").json()
    assert report == {"order_count": 1, "gross_sales_cents": 5000, "discounts_cents": 500,
                      "refunds_cents": 1000, "net_sales_cents": 3500}
