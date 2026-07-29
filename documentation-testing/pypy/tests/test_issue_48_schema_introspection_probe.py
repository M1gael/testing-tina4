# Probe — covers BH-48 (#48). Schema-aware introspection: a table in a NON-public
# PostgreSQL schema must resolve via table_exists()/get_tables()/get_columns().
# Fixed v3.13.14; OUR-verified on 3.13.39 (2026-06-22). Flips red if introspection
# reverts to the pre-fix hardcoded `public` schema (when the whole dotted name was
# matched as one flat tablename, so non-public tables were invisible).
import os

import psycopg2
import pytest

from tina4_python.database.postgres import PostgreSQLAdapter

URL = os.environ.get("TINA4_DATABASE_URL",
                     "postgresql://postgres:tina4test@localhost:5432/tina4testingdb")


def _pg_up():
    try:
        psycopg2.connect(URL).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _pg_up(), reason="PostgreSQL fixture not reachable")


@pytest.fixture
def schema_table():
    c = psycopg2.connect(URL); c.autocommit = True; cur = c.cursor()
    cur.execute("DROP SCHEMA IF EXISTS gift_cards CASCADE")
    cur.execute("CREATE SCHEMA gift_cards")
    cur.execute("CREATE TABLE gift_cards.gift_card "
                "(id SERIAL PRIMARY KEY, code VARCHAR(50), amount NUMERIC)")
    cur.close(); c.close()
    yield
    c = psycopg2.connect(URL); c.autocommit = True; cur = c.cursor()
    cur.execute("DROP SCHEMA IF EXISTS gift_cards CASCADE"); cur.close(); c.close()


def _adapter():
    a = PostgreSQLAdapter()
    a.connect(URL)
    return a


def test_table_exists_resolves_non_public_schema(schema_table):
    a = _adapter()
    assert a.table_exists("gift_cards.gift_card") is True   # pre-fix: False
    assert a.table_exists("gift_cards.nope") is False


def test_get_tables_returns_schema_qualified(schema_table):
    assert "gift_cards.gift_card" in _adapter().get_tables()


def test_get_columns_honours_schema(schema_table):
    cols = {c["name"] for c in _adapter().get_columns("gift_cards.gift_card")}
    assert {"id", "code", "amount"} <= cols
