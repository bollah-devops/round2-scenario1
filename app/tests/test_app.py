"""
test_app.py — pytest suite for the Store API
Run:  pytest test_app.py -v
"""

import json
import pytest

import app as flask_app   # imports the module; gives us access to `cart` & `PRODUCTS`


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Fresh test client for every test.
    Clears the shared in-memory cart before each test so state never leaks.
    """
    flask_app.app.config["TESTING"] = True
    flask_app.cart.clear()
    with flask_app.app.test_client() as c:
        yield c


def post_json(client, path, payload):
    """Convenience wrapper: POST with a JSON body, return the response."""
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
    )


def get_json(response):
    """Decode a response body as JSON regardless of content-type details."""
    return json.loads(response.data)


# ── GET / ────────────────────────────────────────────────────────────────────

class TestWelcome:
    def test_html_response_for_browser(self, client):
        """Browsers (Accept: text/html) should receive the styled HTML page."""
        res = client.get("/", headers={"Accept": "text/html"})
        assert res.status_code == 200
        assert b"<!DOCTYPE html>" in res.data
        assert b"store-api" in res.data

    def test_json_response_for_api_clients(self, client):
        """Clients that accept only JSON should get a JSON overview."""
        res = client.get("/", headers={"Accept": "application/json"})
        assert res.status_code == 200
        body = get_json(res)
        assert body["service"] == "store-api"
        assert body["status"] == "running"
        assert "endpoints" in body

    def test_json_overview_lists_all_five_routes(self, client):
        res = client.get("/", headers={"Accept": "application/json"})
        paths = [ep["path"] for ep in get_json(res)["endpoints"]]
        assert set(paths) == {"/", "/products", "/cart", "/cart/add", "/health"}

    def test_cors_header_present(self, client):
        res = client.get("/", headers={"Accept": "application/json"})
        assert res.headers.get("Access-Control-Allow-Origin") == "*"


# ── GET /products ─────────────────────────────────────────────────────────────

class TestProducts:
    def test_returns_200(self, client):
        res = client.get("/products")
        assert res.status_code == 200

    def test_content_type_is_json(self, client):
        res = client.get("/products")
        assert "application/json" in res.content_type

    def test_returns_all_products(self, client):
        body = get_json(client.get("/products"))
        assert body["count"] == len(flask_app.PRODUCTS)
        assert len(body["products"]) == len(flask_app.PRODUCTS)

    def test_product_shape(self, client):
        """Every product must expose the four expected fields."""
        products = get_json(client.get("/products"))["products"]
        required = {"id", "name", "price", "category"}
        for p in products:
            assert required.issubset(p.keys()), f"Product missing fields: {p}"

    def test_filter_by_peripherals(self, client):
        body = get_json(client.get("/products?category=peripherals"))
        assert body["count"] == 3
        assert all(p["category"] == "peripherals" for p in body["products"])

    def test_filter_by_accessories(self, client):
        body = get_json(client.get("/products?category=accessories"))
        assert body["count"] == 3
        assert all(p["category"] == "accessories" for p in body["products"])

    def test_filter_unknown_category_returns_empty(self, client):
        body = get_json(client.get("/products?category=nonexistent"))
        assert body["count"] == 0
        assert body["products"] == []

    def test_count_matches_products_length(self, client):
        body = get_json(client.get("/products"))
        assert body["count"] == len(body["products"])

    def test_prices_are_positive(self, client):
        products = get_json(client.get("/products"))["products"]
        assert all(p["price"] > 0 for p in products)


# ── GET /cart ─────────────────────────────────────────────────────────────────

class TestCartRead:
    def test_empty_cart_on_fresh_start(self, client):
        body = get_json(client.get("/cart"))
        assert body["item_count"] == 0
        assert body["items"] == []
        assert body["subtotal"] == 0
        assert body["currency"] == "USD"

    def test_returns_200(self, client):
        assert client.get("/cart").status_code == 200

    def test_content_type_is_json(self, client):
        res = client.get("/cart")
        assert "application/json" in res.content_type

    def test_subtotal_reflects_items(self, client):
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 2})
        body = get_json(client.get("/cart"))
        keyboard = next(p for p in flask_app.PRODUCTS if p["id"] == 1)
        assert body["subtotal"] == round(keyboard["price"] * 2, 2)


# ── POST /cart/add ────────────────────────────────────────────────────────────

class TestCartAdd:
    # ── Happy-path ────────────────────────────────────────────────────────────

    def test_add_single_item_returns_201(self, client):
        res = post_json(client, "/cart/add", {"product_id": 1, "quantity": 1})
        assert res.status_code == 201

    def test_response_contains_expected_keys(self, client):
        body = get_json(post_json(client, "/cart/add", {"product_id": 2, "quantity": 1}))
        assert {"message", "cart_item_count", "subtotal"}.issubset(body.keys())

    def test_message_contains_product_name(self, client):
        body = get_json(post_json(client, "/cart/add", {"product_id": 3, "quantity": 1}))
        mouse = next(p for p in flask_app.PRODUCTS if p["id"] == 3)
        assert mouse["name"] in body["message"]

    def test_cart_item_count_increments(self, client):
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 1})
        post_json(client, "/cart/add", {"product_id": 2, "quantity": 1})
        body = get_json(client.get("/cart"))
        assert body["item_count"] == 2

    def test_default_quantity_is_one(self, client):
        """Omitting 'quantity' should default to 1."""
        post_json(client, "/cart/add", {"product_id": 4})
        item = flask_app.cart[0]
        assert item["quantity"] == 1

    def test_adding_same_product_stacks_quantity(self, client):
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 2})
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 3})
        body = get_json(client.get("/cart"))
        # Still one distinct line-item, but quantity = 5
        assert body["item_count"] == 1
        assert body["items"][0]["quantity"] == 5

    def test_subtotal_correct_after_multiple_adds(self, client):
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 1})   # 149.99
        post_json(client, "/cart/add", {"product_id": 6, "quantity": 2})   # 29.00 × 2 = 58.00
        body = get_json(client.get("/cart"))
        assert body["subtotal"] == round(149.99 + 58.00, 2)

    def test_large_quantity(self, client):
        res = post_json(client, "/cart/add", {"product_id": 5, "quantity": 999})
        assert res.status_code == 201
        body = get_json(client.get("/cart"))
        assert body["items"][0]["quantity"] == 999

    # ── Validation errors ─────────────────────────────────────────────────────

    def test_missing_body_returns_400(self, client):
        res = client.post("/cart/add", content_type="application/json", data="")
        assert res.status_code == 400

    def test_non_json_content_type_returns_400(self, client):
        res = client.post("/cart/add", data="product_id=1", content_type="text/plain")
        assert res.status_code == 400

    def test_missing_product_id_returns_400(self, client):
        res = post_json(client, "/cart/add", {"quantity": 1})
        assert res.status_code == 400
        assert "product_id" in get_json(res)["error"].lower()

    def test_unknown_product_id_returns_404(self, client):
        res = post_json(client, "/cart/add", {"product_id": 9999, "quantity": 1})
        assert res.status_code == 404
        assert "9999" in get_json(res)["error"]

    def test_zero_quantity_returns_400(self, client):
        res = post_json(client, "/cart/add", {"product_id": 1, "quantity": 0})
        assert res.status_code == 400

    def test_negative_quantity_returns_400(self, client):
        res = post_json(client, "/cart/add", {"product_id": 1, "quantity": -3})
        assert res.status_code == 400

    def test_float_quantity_returns_400(self, client):
        res = post_json(client, "/cart/add", {"product_id": 1, "quantity": 1.5})
        assert res.status_code == 400

    def test_string_quantity_returns_400(self, client):
        res = post_json(client, "/cart/add", {"product_id": 1, "quantity": "two"})
        assert res.status_code == 400

    def test_null_product_id_returns_400(self, client):
        res = post_json(client, "/cart/add", {"product_id": None, "quantity": 1})
        assert res.status_code == 400

    def test_error_response_contains_error_key(self, client):
        res = post_json(client, "/cart/add", {"quantity": 1})
        assert "error" in get_json(res)


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_status_is_ok(self, client):
        body = get_json(client.get("/health"))
        assert body["status"] == "ok"

    def test_service_name(self, client):
        body = get_json(client.get("/health"))
        assert body["service"] == "store-api"

    def test_timestamp_is_present_and_utc(self, client):
        body = get_json(client.get("/health"))
        assert "timestamp" in body
        assert body["timestamp"].endswith("Z")

    def test_checks_block_present(self, client):
        body = get_json(client.get("/health"))
        assert "checks" in body
        assert "products_loaded" in body["checks"]
        assert "cart_items" in body["checks"]

    def test_products_loaded_count_is_correct(self, client):
        body = get_json(client.get("/health"))
        assert body["checks"]["products_loaded"] == len(flask_app.PRODUCTS)

    def test_cart_items_reflects_state(self, client):
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 1})
        post_json(client, "/cart/add", {"product_id": 2, "quantity": 1})
        body = get_json(client.get("/health"))
        assert body["checks"]["cart_items"] == 2

    def test_content_type_is_json(self, client):
        res = client.get("/health")
        assert "application/json" in res.content_type

    def test_cors_header_present(self, client):
        res = client.get("/health")
        assert res.headers.get("Access-Control-Allow-Origin") == "*"


# ── Cross-route integration ───────────────────────────────────────────────────

class TestIntegration:
    def test_full_shopping_flow(self, client):
        """Add two different products, verify cart totals and health check all agree."""
        # 1. Start empty
        cart_body = get_json(client.get("/cart"))
        assert cart_body["item_count"] == 0

        # 2. Add keyboard × 1
        r1 = post_json(client, "/cart/add", {"product_id": 1, "quantity": 1})
        assert r1.status_code == 201

        # 3. Add webcam × 2
        r2 = post_json(client, "/cart/add", {"product_id": 2, "quantity": 2})
        assert r2.status_code == 201

        # 4. Cart should have 2 line-items
        cart_body = get_json(client.get("/cart"))
        assert cart_body["item_count"] == 2

        # 5. Subtotal: 149.99 + (89.95 × 2)
        expected = round(149.99 + 89.95 * 2, 2)
        assert cart_body["subtotal"] == expected

        # 6. Health check agrees on cart count
        health_body = get_json(client.get("/health"))
        assert health_body["checks"]["cart_items"] == 2

    def test_products_endpoint_unaffected_by_cart_changes(self, client):
        """Adding to cart must not mutate the product catalogue."""
        before = get_json(client.get("/products"))["count"]
        post_json(client, "/cart/add", {"product_id": 1, "quantity": 99})
        after = get_json(client.get("/products"))["count"]
        assert before == after

    def test_cart_isolation_between_tests(self, client):
        """The fixture must clear state: this test always sees an empty cart."""
        body = get_json(client.get("/cart"))
        assert body["item_count"] == 0
        assert body["subtotal"] == 0