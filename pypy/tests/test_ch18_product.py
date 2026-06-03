# ch18 section 4 — Testing ORM Models
# This snippet is broken end-to-end as written (see PY-18-07). The PATCHES block
# below works around two doc bugs so the tests can run. To reproduce the original
# bugs, delete the entire PATCHES block and the `from src.orm.product import
# Product` line just below it — the verbatim-from-chapter code starts at the
# `from tina4_python.test import ...` line.
#
# ============================== PATCHES ==============================
#
# PATCH [PY-18-07a]: the chapter NEVER imports `Product`. Without this line,
# every test fails with `NameError: name 'Product' is not defined`.
from src.orm.product import Product

# PATCH [PY-18-07b]: the chapter claims `tina4 test` auto-binds a separate test
# database at `data/test.db` and resets it between runs. Neither happens — no DB
# is bound by default and no schema is created. The three lines below set the
# DB URL via env var, ensure the data/ dir exists, and create the products table
# so ProductTest can save/load/delete. Without these, every test fails with
# `RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL`.
import os
os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")
os.makedirs("data", exist_ok=True)
Product.create_table()
#
# ============================ END PATCHES ============================

# Verbatim chapter code starts here:
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none

class ProductTest(Test):

    def test_create_product(self):
        product = Product()
        product.name = "Test Widget"
        product.category = "Testing"
        product.price = 19.99
        product.in_stock = True
        product.save()

        assert_not_none(product.id, "Product should have an ID after save")
        assert_true(product.id > 0, "Product ID should be positive")

    def test_load_product(self):
        product = Product()
        product.name = "Load Test Widget"
        product.category = "Testing"
        product.price = 29.99
        product.save()

        loaded = Product.find(product.id)

        assert_equal(loaded.name, "Load Test Widget", "Name should match")
        assert_equal(loaded.category, "Testing", "Category should match")
        assert_equal(loaded.price, 29.99, "Price should match")

    def test_update_product(self):
        product = Product()
        product.name = "Update Test Widget"
        product.price = 10.00
        product.save()

        product_id = product.id

        product.name = "Updated Widget"
        product.price = 15.00
        product.save()

        reloaded = Product.find(product_id)

        assert_equal(reloaded.name, "Updated Widget", "Name should be updated")
        assert_equal(reloaded.price, 15.00, "Price should be updated")

    def test_delete_product(self):
        product = Product()
        product.name = "Delete Me"
        product.price = 5.00
        product.save()

        product_id = product.id
        product.delete()

        gone = Product.find(product_id)

        assert_true(gone is None, "Deleted product should not be loadable")

    def test_select_with_filter(self):
        p1 = Product()
        p1.name = "Filter Test A"
        p1.category = "FilterCat"
        p1.price = 10.00
        p1.save()

        p2 = Product()
        p2.name = "Filter Test B"
        p2.category = "FilterCat"
        p2.price = 20.00
        p2.save()

        # PATCH [PY-18-07c]: chapter shows `products, count = Product.where(...)` —
        # a 2-tuple return. Real where() returns a flat list by default; to get the
        # (records, count) tuple shown in the chapter, you must pass with_count=True
        # (parameter never mentioned anywhere in chapter). To reproduce the original
        # ValueError ("too many values to unpack (expected 2)"), remove
        # `, with_count=True` from the call below.
        products, count = Product.where("category = ?", ["FilterCat"], with_count=True)

        assert_true(len(products) >= 2, "Should find at least 2 FilterCat products")

        names = [p.name for p in products]
        assert_true("Filter Test A" in names, "Should include Filter Test A")
        assert_true("Filter Test B" in names, "Should include Filter Test B")