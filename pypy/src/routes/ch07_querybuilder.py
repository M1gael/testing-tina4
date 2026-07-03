# ch07 QueryBuilder — S1 "The Factory: from_table()" + S2 "Choosing Columns: select()".
# Live, browser-navigable mock of the verbatim chapter snippets, served under
# `tina4 serve`. Doc: 07-query-builder.md S1 (lines 9-22) + S2 (lines 25-43).
#
# S1 shows `QueryBuilder.from_table("users", db)`; the chapter says imports/`db`
# come "the same Database object you use everywhere else". Under `tina4 serve`
# the global ORM database is already bound from .env, so the no-db form
# (from_table("users")) also exercises S1's documented global-ORM fallback.
import os

from tina4_python.core.router import get
from tina4_python.database import Database
from tina4_python.query_builder import QueryBuilder


@get("/api/ch07/qb/select-demo")
async def qb_select_demo(request, response):
    # S1 verbatim: explicit db argument.
    db = Database(os.environ["TINA4_DATABASE_URL"])

    return response({
        # --- S1 The Factory: from_table() ---
        "s1_explicit_db_sql": QueryBuilder.from_table("users", db).to_sql(),
        "s1_global_fallback_sql": QueryBuilder.from_table("users").to_sql(),  # no db -> global
        "s1_fresh_instance": (
            QueryBuilder.from_table("users", db)
            is not QueryBuilder.from_table("users", db)
        ),
        "s1_chainable": (
            QueryBuilder.from_table("users", db).select("id") is not None
        ),
        # --- S2 Choosing Columns: select() ---
        "s2_default_star": QueryBuilder.from_table("users", db).to_sql(),
        "s2_select_narrow": (
            QueryBuilder.from_table("users", db).select("id", "name", "email").to_sql()
        ),
        "s2_select_replace": (
            QueryBuilder.from_table("users", db).select("id", "name").select("email").to_sql()
        ),
    })
