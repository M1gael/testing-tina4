# Verbatim-impl test — Chapter 6 ORM, "QueryBuilder Integration" (06-orm.md:1376-1403).
# The trailing section: Model.query() returns a QueryBuilder for a fluent API; the
# full builder (joins/grouping/having/Mongo) is deferred to Ch07. Run against live PG.
#
# All four documented forms behave as documented on tina4-python 3.13.39:
#   query() -> QueryBuilder
#   .select().where().order_by().limit().get() -> result rows
#   .where().first()  -> single match
#   .where().count()  -> int
#   .where().exists() -> bool
# Note (minor, no doc claim broken): get()/first() return dict / DatabaseResult
# rows, NOT ORM model instances (unlike find_by_id/find/where). This section shows
# no attribute access, so nothing in it is contradicted; return types are Ch07's.
import os

import psycopg2
import pytest

from tina4_python.orm import ORM, IntegerField, StringField, BooleanField


class QbUser(ORM):
    table_name = "qb_users"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    email = StringField(default="")
    role = StringField(default="user")
    active = BooleanField(default=True)


def _exec(sql):
    c = psycopg2.connect(os.environ["TINA4_DATABASE_URL"])
    c.autocommit = True
    cur = c.cursor()
    cur.execute(sql)
    cur.close()
    c.close()


@pytest.fixture(autouse=True)
def _schema():
    _exec("DROP TABLE IF EXISTS qb_users CASCADE")
    QbUser.create_table()
    for n, e, r, a in [("Alice", "alice@example.com", "admin", True),
                       ("Bob", "bob@example.com", "user", True),
                       ("Cara", "cara@example.com", "admin", False)]:
        u = QbUser(); u.name = n; u.email = e; u.role = r; u.active = a; u.save()
    yield
    _exec("DROP TABLE IF EXISTS qb_users CASCADE")


def test_query_returns_querybuilder():
    assert type(QbUser.query()).__name__ == "QueryBuilder"


# --- get(): select + where + order_by + limit (06-orm.md:1382-1387) ---
def test_get_fluent_chain():
    results = QbUser.query() \
        .select("id", "name", "email") \
        .where("active = ?", [True]) \
        .order_by("name") \
        .limit(50) \
        .get()
    rows = list(results)
    assert len(rows) == 2                       # Cara is inactive -> excluded
    assert [r["name"] for r in rows] == ["Alice", "Bob"]  # ordered by name
    assert set(rows[0].keys()) == {"id", "name", "email"}  # selected columns only


# --- first(): single matching record (06-orm.md:1390-1392) ---
def test_first_returns_match():
    user = QbUser.query() \
        .where("email = ?", ["alice@example.com"]) \
        .first()
    assert user is not None
    assert user["name"] == "Alice"


# --- count() (06-orm.md:1395-1397) ---
def test_count():
    total = QbUser.query() \
        .where("role = ?", ["admin"]) \
        .count()
    assert total == 2  # Alice + Cara


# --- exists() (06-orm.md:1400-1402) ---
def test_exists():
    assert QbUser.query().where("email = ?", ["alice@example.com"]).exists() is True
    assert QbUser.query().where("email = ?", ["nope@example.com"]).exists() is False
