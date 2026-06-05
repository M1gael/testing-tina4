# ch18 section 5 — Testing Routes
# VERBATIM from the chapter. PY-18-08 was fixed in tina4-python 3.13.4 — the
# chapter now uses `resp.status` (not `.status_code`) and `self.post(..., json={...})`
# (keyword body, not positional). No code patches required.
#
# Note: most tests still fail at runtime because /api/products etc. are not
# routes defined in a fresh `tina4 init python .` scaffold. That's a separate
# concern from PY-18-08 — the chapter doesn't show how to define those routes;
# it assumes the reader implemented earlier chapters (Ch 2 routing, Ch 6 ORM).
# Only /health is part of the default scaffold.

from tina4_python.test import Test, assert_equal, assert_true, assert_not_none
import json

class RouteTest(Test):

    def test_health_endpoint(self):
        resp = self.get("/health")

        assert_equal(resp.status, 200, "Health check should return 200")

        body = json.loads(resp.body)
        assert_equal(body["status"], "ok", "Status should be 'ok'")
        assert_not_none(body.get("version"), "Should include version")

    def test_get_products(self):
        resp = self.get("/api/products")

        assert_equal(resp.status, 200, "Should return 200")

        body = json.loads(resp.body)
        assert_true("data" in body or "products" in body, "Should contain product data")

    def test_create_product(self):
        resp = self.post("/api/products", json={
            "name": "Route Test Product",
            "category": "Testing",
            "price": 42.00
        })

        assert_equal(resp.status, 201, "Should return 201 Created")

        body = json.loads(resp.body)
        assert_equal(body["name"], "Route Test Product", "Name should match")
        assert_equal(body["price"], 42.00, "Price should match")

    def test_get_product_not_found(self):
        resp = self.get("/api/products/99999")

        assert_equal(resp.status, 404, "Should return 404 for missing product")

    def test_create_product_validation(self):
        resp = self.post("/api/products", json={})

        assert_equal(resp.status, 400, "Should return 400 for empty body")

    def test_delete_product(self):
        # Create a product first
        create_resp = self.post("/api/products", json={
            "name": "To Be Deleted",
            "price": 1.00
        })
        body = json.loads(create_resp.body)
        product_id = body["id"]

        # Delete it
        delete_resp = self.delete(f"/api/products/{product_id}")
        assert_equal(delete_resp.status, 204, "Should return 204 No Content")

        # Verify it is gone
        get_resp = self.get(f"/api/products/{product_id}")
        assert_equal(get_resp.status, 404, "Should return 404 after deletion")
