# ch18 section 10 — Testing Best Practices
# Verbatim implementation of the three documented patterns:
#   - Test One Thing Per Test (S10 lines 645-660)
#   - Use Descriptive Assertion Messages (S10 lines 663-671)  [text only, no code to run]
#   - Isolate Tests (S10 lines 673-694)
#
# The chapter snippets are illustrative ("Good:" / "Bad:"), not standalone test
# files — they show patterns. This file groups the "Good" snippets into one
# class so pytest discovers them. The bad-pattern snippets are intentionally
# omitted (the chapter labels them as anti-examples).

import json
from tina4_python.test import Test, assert_equal, assert_true
from src.orm.Product import Product


class BestPracticesTest(Test):

    # ── 1. Test One Thing Per Test (S10 lines 645-660) ──────────────────

    def test_create_product_returns_201(self):
        resp = self.post("/api/products", json={"name": "Widget", "price": 9.99})
        assert_equal(resp.status, 201, "Should return 201")

    def test_create_product_returns_created_product(self):
        resp = self.post("/api/products", json={"name": "Widget", "price": 9.99})
        body = json.loads(resp.body)
        assert_equal(body["name"], "Widget", "Should return the product name")

    # ── 3. Isolate Tests (S10 lines 673-694) ────────────────────────────

    def test_delete_product(self):
        product = Product()
        product.name = "Temporary"
        product.price = 1.00
        product.save()

        product.delete()

        check = Product.find(product.id)
        assert_true(check is None, "Product should be deleted")
