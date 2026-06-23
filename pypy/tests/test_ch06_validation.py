# Verbatim-impl test — Chapter 6 ORM, S12 "Input Validation" (06-orm.md:1033-1078).
# Implemented exactly as the section shows.
#
# S12's subject is validate(): "Call validate() before save() and the ORM checks
# every constraint" (06-orm.md:1035); on failure it "returns a list of error
# messages" (06-orm.md:1067). validate() is pure Python over the field rules and
# needs no database, so the verbatim Product below is exercised directly.
#
# S12's Product declares table_name="products" — the same table the Ch18
# supporting Product (src/orm/Product.py, created at import time) owns with a
# different schema (PY-06-05 collision family). To prove the save() path
# (06-orm.md:1063) without clobbering that shared table in the full suite, the
# save check runs against an isolated subclass table.
#
# What the ORM showed (tina4-python 3.13.39):
#   - validate() returns a list, one entry per failed constraint, and catches
#     every documented rule (required / min_length / regex / min_value / choices);
#     valid input -> []. Behaviour faithful.
#   - BUT the message WORDING does NOT match the doc's JSON example (PY-06-24):
#       doc:    "name: Must be at least 2 characters"
#       actual: "Field 'name': minimum length is 2, got 1"
#     Same divergence class as PY-06-20 (S9 validation-detail wording).
#   test_validate_message_format_py_06_24 asserts the ACTUAL format AND that the
#   doc-claimed strings are absent, so it flips if the framework or doc aligns.
import os

import psycopg2
import pytest

from tina4_python.orm import ORM, IntegerField, StringField, NumericField


# --- verbatim S12 model (06-orm.md:1038-1048) ---
class Product(ORM):
    table_name = "products"

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, min_length=2, max_length=200)
    sku = StringField(required=True, regex=r"^[A-Z]{2}-\d{4}$")  # e.g., EL-1234
    price = NumericField(required=True, min_value=0.01, max_value=999999.99)
    category = StringField(choices=["Electronics", "Kitchen", "Office", "Fitness"])


def _all_bad():
    # mirrors the doc error example (06-orm.md:1070-1077): every field invalid.
    p = Product()
    p.name = "A"          # min_length=2 -> too short
    p.sku = "bad"         # fails regex ^[A-Z]{2}-\d{4}$
    p.price = 0.0         # below min_value 0.01
    p.category = "Nope"   # not in choices
    return p


# --- documented claim: validate() returns a list of error messages (06-orm.md:1067) ---
def test_validate_returns_list_of_errors():
    errs = _all_bad().validate()
    assert isinstance(errs, list)
    assert len(errs) == 4  # one per failed constraint


# --- documented claim: "checks every constraint" (06-orm.md:1035) — behaviour faithful ---
def test_validate_catches_every_constraint():
    blob = " | ".join(_all_bad().validate())
    assert "name" in blob       # min_length
    assert "sku" in blob        # regex
    assert "price" in blob      # min_value
    assert "category" in blob   # choices


def test_validate_passes_on_valid_input():
    g = Product()
    g.name = "Widget"
    g.sku = "EL-1234"
    g.price = 9.99
    g.category = "Electronics"
    assert g.validate() == []


def test_validate_flags_missing_required_fields():
    # category has no required=True, so only name/sku/price are reported.
    errs = Product().validate()
    blob = " | ".join(errs)
    assert "name" in blob and "sku" in blob and "price" in blob
    assert len(errs) == 3


# --- PY-06-24 sentinel: actual message wording != doc's JSON example ---
def test_validate_message_format_py_06_24():
    errs = _all_bad().validate()
    blob = "\n".join(errs)

    # actual format the framework emits (3.13.39)
    assert "Field 'name': minimum length is 2, got 1" in errs
    assert "Field 'sku': value does not match pattern" in blob
    assert "Field 'price': minimum value is 0.01, got 0.0" in errs
    assert "must be one of ['Electronics', 'Kitchen', 'Office', 'Fitness']" in blob

    # doc-claimed strings (06-orm.md:1072-1075) are NOT produced
    assert "name: Must be at least 2 characters" not in blob
    assert "price: Must be at least 0.01" not in blob
    assert "category: Must be one of: Electronics, Kitchen, Office, Fitness" not in blob


# --- save() success path (06-orm.md:1063): valid model persists, id assigned ---
# Isolated table so the full suite's shared `products` (Ch18) is untouched.
# Same S12 fields, distinct table_name (fields are collected per-class from the
# class namespace, so a bare subclass would carry no _fields).
class _ProductSaveProbe(ORM):
    table_name = "products_s12_save"

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, min_length=2, max_length=200)
    sku = StringField(required=True, regex=r"^[A-Z]{2}-\d{4}$")
    price = NumericField(required=True, min_value=0.01, max_value=999999.99)
    category = StringField(choices=["Electronics", "Kitchen", "Office", "Fitness"])


def _exec(sql):
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    c.autocommit = True
    cur = c.cursor()
    cur.execute(sql)
    cur.close()
    c.close()


@pytest.fixture
def _save_table():
    _exec("DROP TABLE IF EXISTS products_s12_save CASCADE")
    _ProductSaveProbe.create_table()
    yield
    _exec("DROP TABLE IF EXISTS products_s12_save CASCADE")


def test_valid_product_saves(_save_table):
    g = _ProductSaveProbe()
    g.name = "Widget"
    g.sku = "EL-1234"
    g.price = 9.99
    g.category = "Electronics"
    assert g.validate() == []
    g.save()
    assert g.id is not None
    assert _ProductSaveProbe.find_by_id(g.id) is not None
