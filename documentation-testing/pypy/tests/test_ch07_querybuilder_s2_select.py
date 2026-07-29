# QA-audit test — Chapter 7 QueryBuilder, S2 "Choosing Columns: select()".
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/07-query-builder.md (S2, lines 25-43)
# Framework      : tina4_python.query_builder (READ-ONLY — never modified)
#
# Per Protocol rule 11 (strict traceability) every test opens with the EXACT
# quoted claim it verifies plus that doc file path. S2's claims are about the SQL
# the builder produces ("This selects only email, not id, name, email"); the SQL
# is read with to_sql() — the inspection method the chapter introduces in S8 — used
# here purely as the observation tool for S2's documented SQL shape. No execution
# needed, so no table rows required.
import os

import pytest

from tina4_python.query_builder import QueryBuilder


@pytest.fixture
def db():
    from tina4_python.database import Database
    return Database(os.environ["TINA4_DATABASE_URL"])


def test_default_selects_all_columns_star(db):
    """07-query-builder.md (S2): "By default, QueryBuilder selects all columns
    (`*`)." (line 27) and "If you want all columns, skip `select()` entirely. The
    default is `*`." (line 43)
    """
    sql = QueryBuilder.from_table("users", db).to_sql()
    assert sql == "SELECT * FROM users", f"default is SELECT * ; got {sql!r}"


def test_select_narrows_with_separate_column_arguments(db):
    """07-query-builder.md (S2): the verbatim snippet
    `QueryBuilder.from_table("users", db).select("id", "name", "email")` and
    "Pass column names as separate arguments, not a list." (lines 30-34)
    """
    sql = QueryBuilder.from_table("users", db).select("id", "name", "email").to_sql()
    assert sql == "SELECT id, name, email FROM users", (
        f"select() narrows to the named columns; got {sql!r}"
    )


def test_each_select_replaces_the_previous_selection(db):
    """07-query-builder.md (S2): "Each call to `select()` replaces the previous
    column selection." with the verbatim snippet
    `.select("id", "name").select("email")` annotated
    "# This selects only "email", not "id", "name", "email"" (lines 34-41)
    """
    sql = QueryBuilder.from_table("users", db).select("id", "name").select("email").to_sql()
    assert sql == "SELECT email FROM users", (
        f"the second select() replaces the first (only 'email'); got {sql!r}"
    )


def test_skipping_select_entirely_defaults_to_star(db):
    """07-query-builder.md (S2): "If you want all columns, skip `select()`
    entirely. The default is `*`." (line 43) — a chain with no select() at all.
    """
    sql = QueryBuilder.from_table("users", db).to_sql()
    assert sql == "SELECT * FROM users", f"no select() => SELECT * ; got {sql!r}"
