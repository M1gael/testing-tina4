# QA-audit test — Chapter 7 QueryBuilder, S1 "The Factory: from_table()".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/07-query-builder.md (S1, lines 9-22)
# Framework      : tina4_python.query_builder (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. File backend / live PG
# (tina4testingdb, the suite default bound by conftest). Implement-as-reader:
# the verbatim S1 snippets are run and observed; nothing the chapter doesn't show.
import os
import subprocess
import sys

import pytest

from tina4_python.query_builder import QueryBuilder


@pytest.fixture
def db():
    """The `Database` object the chapter calls `db` — the same one used in Ch5/Ch6.
    conftest loads pypy/.env into os.environ, so TINA4_DATABASE_URL is bound."""
    from tina4_python.database import Database
    return Database(os.environ["TINA4_DATABASE_URL"])


def test_from_table_returns_a_querybuilder_instance(db):
    """07-query-builder.md (S1 The Factory): the verbatim snippet
    `from tina4_python.query_builder import QueryBuilder` /
    `qb = QueryBuilder.from_table("users", db)` — "`from_table()` returns a fresh
    `QueryBuilder` instance." (lines 14-21)
    """
    qb = QueryBuilder.from_table("users", db)
    assert isinstance(qb, QueryBuilder), "from_table() returns a QueryBuilder"


def test_from_table_returns_a_fresh_instance_each_call(db):
    """07-query-builder.md (S1): "`from_table()` returns a fresh `QueryBuilder`
    instance." (line 21) — two calls must not be the same object.
    """
    qb1 = QueryBuilder.from_table("users", db)
    qb2 = QueryBuilder.from_table("users", db)
    assert qb1 is not qb2, "each from_table() is a fresh instance"


def test_methods_return_the_same_instance_so_you_can_chain(db):
    """07-query-builder.md (S1): "Every method you call on it returns the same
    instance, so you can chain." (lines 21-22)
    """
    qb = QueryBuilder.from_table("users", db)
    assert qb.select("id", "name") is qb, "select() returns the same instance"
    assert qb.where("active = ?", [1]) is qb, "where() returns the same instance"


def test_omitting_db_falls_back_to_the_global_orm_database():
    """07-query-builder.md (S1): "If you omit the database, QueryBuilder will fall
    back to the global ORM database (set via `bind_database()`)." (line 19)
    Bind the global, then build with NO db argument and execute — it must work.
    """
    from tina4_python.database import Database
    from tina4_python.orm.model import bind_database

    bind_database(Database(os.environ["TINA4_DATABASE_URL"]))
    qb = QueryBuilder.from_table("users")  # NO db argument
    result = qb.select("id").limit(1).get()
    assert result is not None, "execute succeeds via the global ORM database fallback"


def test_no_db_and_no_global_raises_runtimeerror_on_execute():
    """07-query-builder.md (S1): "If neither exists, it raises a `RuntimeError`
    when you try to execute." (line 19)

    Run in a clean subprocess with NO TINA4_DATABASE_URL and no bind_database()
    call, so there is neither an explicit db nor a global ORM database — then
    execute. (The suite's conftest binds a global db in-process, so this claim is
    only observable in an unbound interpreter.)
    """
    code = (
        "import os; os.environ.pop('TINA4_DATABASE_URL', None)\n"
        "from tina4_python.query_builder import QueryBuilder\n"
        "qb = QueryBuilder.from_table('users')\n"
        "try:\n"
        "    qb.get()\n"
        "    print('NO_ERROR')\n"
        "except RuntimeError as e:\n"
        "    print('RUNTIMEERROR')\n"
        "except Exception as e:\n"
        "    print('OTHER:' + type(e).__name__)\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "TINA4_DATABASE_URL"}
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=30
    ).stdout.strip()
    assert out == "RUNTIMEERROR", (
        f"execute with neither db nor global must raise RuntimeError; got {out!r}"
    )
