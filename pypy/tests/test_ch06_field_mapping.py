# Verbatim-impl test — Chapter 6 ORM, S2 "Field Mapping",
# "_get_db_column and _get_db_data", "find() vs where()", and
# "auto_map and Case Conversion Utilities".
#
# The chapter's field-mapping User (user_accounts) and Account (ACCOUNTS)
# examples are illustrative (no "Create src/orm/..." instruction); they are
# defined inline here verbatim. A standalone src/orm/user.py would also collide
# with the existing ch18 src/orm/User.py on a case-insensitive filesystem.
import os

import psycopg2
import pytest

from tina4_python.orm import ORM, Field, IntegerField, StringField
from tina4_python.orm.model import snake_to_camel, camel_to_snake


class User(ORM):
    table_name = "user_accounts"
    field_mapping = {
        "first_name": "fname",      # Python attr -> DB column
        "last_name": "lname",
        "email_address": "email",
    }

    id = IntegerField(primary_key=True, auto_increment=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email_address = StringField(required=True)


class Account(ORM):
    table_name = "ACCOUNTS"
    field_mapping = {
        "account_no":   "ACCOUNTNO",
        "store_name":   "STORENAME",
        "credit_limit": "CREDITLIMIT",
    }
    account_no   = StringField()
    store_name   = StringField()
    credit_limit = Field(float, default=0.0)


def _drop(*tables):
    conn = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    for t in tables:
        cur.execute(f'DROP TABLE IF EXISTS {t} CASCADE')
    cur.close()
    conn.close()


@pytest.fixture(autouse=True, scope="module")
def _schema():
    _drop("user_accounts", '"ACCOUNTS"', "accounts")
    User.create_table()
    Account.create_table()
    yield
    # No teardown drop — leave tables + rows visible after the run.


@pytest.fixture(autouse=True)
def _clean():
    for u in User.all():
        u.delete()
    yield


# --- Case conversion utilities ---
def test_snake_to_camel():
    assert snake_to_camel("first_name") == "firstName"


def test_camel_to_snake():
    assert camel_to_snake("firstName") == "first_name"


# --- _get_db_column / _get_db_data ---
def test_get_db_column():
    account = Account()
    assert account._get_db_column("account_no") == "ACCOUNTNO"


def test_get_db_data():
    account = Account()
    account.account_no = "A001"
    account.store_name = "Main Store"
    account.credit_limit = 5000.0
    data = account._get_db_data()
    assert data["ACCOUNTNO"] == "A001"
    assert data["STORENAME"] == "Main Store"
    assert data["CREDITLIMIT"] == 5000.0


# --- field_mapping round-trip via save / find_by_id ---
def test_field_mapping_roundtrip():
    u = User()
    u.first_name = "Ada"
    u.last_name = "Lovelace"
    u.email_address = "ada@example.com"
    u.save()
    got = User.find_by_id(u.id)
    assert got.first_name == "Ada"
    assert got.email_address == "ada@example.com"


# --- find() uses Python attr names (translated via field_mapping) ---
def test_find_uses_python_attr_names():
    User.create(first_name="Grace", last_name="Hopper", email_address="grace@example.com")
    rows = User.find({"first_name": "Grace"})
    assert len(rows) == 1
    assert rows[0].last_name == "Hopper"


# --- where() uses raw DB column names ---
def test_where_uses_db_column_names():
    User.create(first_name="Alan", last_name="Turing", email_address="alan@example.com")
    rows = User.where("fname = ?", ["Alan"])
    assert len(rows) == 1


# --- auto_map flag exists on the ORM base (documented no-op in Python) ---
def test_auto_map_flag_present():
    assert hasattr(User, "auto_map")
