# ch18 section 5 — Testing Routes
# Section 5 documents a test client API that doesn't match what tina4_python.test
# actually exposes (PY-18-08). The PATCH lines below work around two issues:
#
#   - PY-18-08a: self.post(path, body_dict) requires keyword form `json=`/`body=`.
#                Without the patch: TypeError: Test.post() takes 2 positional
#                arguments but 3 were given.
#   - PY-18-08b: TestResponse has no `status_code` attribute. Real attr is `status`.
#                Without the patch: AttributeError: 'TestResponse' object has no
#                attribute 'status_code'.
#
# To restore the docs-verbatim file, swap each PATCH line back to the OLD line
# shown right above it.
#
# Note: most tests still fail after these patches because /api/products etc. are
# not routes defined in a fresh `tina4 init python .` scaffold. That's a
# separate concern from PY-18-08 — the chapter doesn't show how to define those
# routes; it assumes the reader implemented earlier chapters (Ch 2 routing, Ch 6
# ORM). Only /health is part of the default scaffold.

from tina4_python.test import Test, assert_equal, assert_true, assert_not_none
import json

class RouteTest(Test):

    def test_health_endpoint(self):
        resp = self.get("/health")

        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(resp.status_code, 200, "Health check should return 200")
        assert_equal(resp.status, 200, "Health check should return 200")

        body = json.loads(resp.body)
        assert_equal(body["status"], "ok", "Status should be 'ok'")
        assert_not_none(body.get("version"), "Should include version")

    def test_get_products(self):
        resp = self.get("/api/products")

        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(resp.status_code, 200, "Should return 200")
        assert_equal(resp.status, 200, "Should return 200")

        body = json.loads(resp.body)
        assert_true("data" in body or "products" in body, "Should contain product data")

    def test_create_product(self):
        # PATCH [PY-18-08a]: positional body → keyword json=
        # OLD: resp = self.post("/api/products", {
        # OLD:     "name": "Route Test Product",
        # OLD:     "category": "Testing",
        # OLD:     "price": 42.00
        # OLD: })
        resp = self.post("/api/products", json={
            "name": "Route Test Product",
            "category": "Testing",
            "price": 42.00
        })

        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(resp.status_code, 201, "Should return 201 Created")
        assert_equal(resp.status, 201, "Should return 201 Created")

        body = json.loads(resp.body)
        assert_equal(body["name"], "Route Test Product", "Name should match")
        assert_equal(body["price"], 42.00, "Price should match")

    def test_get_product_not_found(self):
        resp = self.get("/api/products/99999")

        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(resp.status_code, 404, "Should return 404 for missing product")
        assert_equal(resp.status, 404, "Should return 404 for missing product")

    def test_create_product_validation(self):
        # PATCH [PY-18-08a]: positional body → keyword json=
        # OLD: resp = self.post("/api/products", {})
        resp = self.post("/api/products", json={})

        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(resp.status_code, 400, "Should return 400 for empty body")
        assert_equal(resp.status, 400, "Should return 400 for empty body")

    def test_delete_product(self):
        # Create a product first
        # PATCH [PY-18-08a]: positional body → keyword json=
        # OLD: create_resp = self.post("/api/products", {
        # OLD:     "name": "To Be Deleted",
        # OLD:     "price": 1.00
        # OLD: })
        create_resp = self.post("/api/products", json={
            "name": "To Be Deleted",
            "price": 1.00
        })
        body = json.loads(create_resp.body)
        product_id = body["id"]

        # Delete it
        delete_resp = self.delete(f"/api/products/{product_id}")
        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(delete_resp.status_code, 204, "Should return 204 No Content")
        assert_equal(delete_resp.status, 204, "Should return 204 No Content")

        # Verify it is gone
        get_resp = self.get(f"/api/products/{product_id}")
        # PATCH [PY-18-08b]: resp.status_code → resp.status
        # OLD: assert_equal(get_resp.status_code, 404, "Should return 404 after deletion")
        assert_equal(get_resp.status, 404, "Should return 404 after deletion")
