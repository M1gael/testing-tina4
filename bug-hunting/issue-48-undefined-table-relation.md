# Issue #48 — Database Table Does Not Exist

**Upstream:** https://github.com/tina4stack/tina4-python/issues/48
**Reporter:** SAB13711 (same reporter as #46, #47)
**Reported:** 2026-06-10T11:46:08Z
**Framework version under test:** tina4-python **3.13.8**
**Status:** **pivoted 2026-06-10 after OP response** — initial "user typo" hypothesis broken; investigation re-opened on connection-target mismatch angle. Awaiting OP env-confirmation reply. See "Update 2026-06-10" section at end of file.

---

## Reporter's symptom

```
2026-06-10T11:41:05.014Z [ERROR] PostgreSQL query failed: UndefinedTable: relation "gift_cards.gift_card" does not exist
LINE 1: SELECT * FROM gift_cards.gift_card WHERE created_by_email = ...
{"sql": "SELECT * FROM gift_cards.gift_card WHERE created_by_email = %s AND is_deleted = 0 LIMIT %s OFFSET %s",
 "params": ["schalk@codeinfinity.co.za", 20, 0]}
```

Reporter: *"I have a database table that definitely exists in the postgres db, but i get this error."*

Notes on the log shape:
- Log format is the v3.13.6 `_on_query_error` wrapper output — this error surfaces *because* the BH-46 visibility fix landed. Pre-3.13.6 this would have been hidden behind the cascade.
- `is_deleted = 0` filter + `gift_cards`/`gift_card`-shaped table name → same reporter, same domain object as #46.
- SQL emits `gift_cards.gift_card` as a single dotted identifier — PG parses this as schema=`gift_cards`, table=`gift_card`.

## Empirical investigation

Framework table-name resolution at `tina4_python/orm/model.py:246-258`:

```python
@classmethod
def _get_table(cls) -> str:
    """Get table name — defaults to lowercase class name."""
    if cls.table_name:
        return cls.table_name
    import os
    name = cls.__name__.lower()
    if os.environ.get("TINA4_ORM_PLURAL_TABLE_NAMES", "").lower() in ("true", "1", "yes"):
        name += "s"
    return name
```

`where()` (`model.py:613-615`) interpolates the result verbatim into `SELECT * FROM {table}`. No quoting, no transformation, no schema-prefix injection anywhere in the ORM or `connection.py`.

### Trial matrix (live PG 18, table `gift_cards` exists in `public` schema)

| `table_name` value | Class | Resolved table | Generated SQL | Result |
|---|---|---|---|---|
| `"gift_cards"` | `GiftCard` | `gift_cards` | `SELECT * FROM gift_cards ...` | Works |
| `"gift_cards.gift_card"` | `GiftCard` | `gift_cards.gift_card` | `SELECT * FROM gift_cards.gift_card ...` | **Byte-identical to reporter's error** |
| `'"gift_cards"."gift_card"'` (quoted) | `GiftCard` | same | `SELECT * FROM "gift_cards"."gift_card" ...` | Same error — PG still parses as schema-qualified |
| `""` (default) | `GiftCard` | `giftcard` | `SELECT * FROM giftcard ...` | `relation "giftcard" does not exist` |
| `""` + `TINA4_ORM_PLURAL_TABLE_NAMES=true` | `GiftCard` | `giftcards` | `SELECT * FROM giftcards ...` | `relation "giftcards" does not exist` |

The byte-match is at trial 2: setting `table_name = "gift_cards.gift_card"` literally on a model produces the exact `relation "gift_cards.gift_card" does not exist` error in the reporter's log.

## Most likely cause

Reporter has `table_name = "gift_cards.gift_card"` literally in their model (e.g. `src/orm/GiftCard.py`). Framework respects it as-is — `_get_table()` returns the string verbatim with no transformation.

Likely confusion path: PostgreSQL schema-qualified syntax (`schema.table`) → reporter wrote `"gift_cards.gift_card"` thinking schema=`gift_cards` (intuiting from the table they'd seen), table=`gift_card` (intuiting from the singular class name). PG expects this to mean *"the `gift_card` relation inside the `gift_cards` schema"* — and reports `does not exist` because their actual setup is the `gift_cards` table in the `public` schema.

## Adversarial disproof attempts (thorough round)

| Tried to break the hypothesis | Result |
|---|---|
| Maybe the framework injects schema dots automatically anywhere — not just ORM dir. | Broader repo grep across `tina4_python/` (ORM + query_builder + database adapters + CRUD + cli + migration + mcp): zero matches for f-string dot-concatenation between table-like names. `_get_table()` returns `cls.table_name` verbatim. `QueryBuilder._table` (`query_builder/__init__.py:27`) stores it raw. |
| Maybe a `TINA4_DB_SCHEMA` / `TINA4_SCHEMA` / `PGSCHEMA` / `search_path` env var produces the dotted form. | None exist. Only env vars: `TINA4_ORM_PLURAL_TABLE_NAMES`, `TINA4_DATABASE_URL`, `TINA4_DATABASE_USERNAME`, `TINA4_DATABASE_PASSWORD`. |
| Maybe `_translate_sql` rewrites table refs during PG-dialect translation. | Source-read of `postgres.py:411-420`: `_translate_sql` only calls `SQLTranslator.placeholder_style`, `auto_increment_syntax`, `boolean_to_int`. None touch table refs — empirically verified by running each transform on `"SELECT * FROM my_table WHERE x = ?"`; `my_table` preserved across all three. |
| Maybe ORM metaclass (`ORMMeta` at `model.py:77-154`) mutates `table_name`. | Source-read: metaclass only collects `Field` instances, sets up relationships, auto-registers CRUD if `auto_crud=True`. `table_name` is never read or modified. |
| Maybe `tina4 generate model GiftCard` scaffolds a dotted `table_name`. | Verified empirically (`tina4 generate model TestModel123`) — scaffold contains no `table_name` line at all. Reporter would have added it manually. |
| Maybe class name → table name resolution generates a dotted form. | Trials 4+5: `GiftCard` default → `giftcard`; with pluralization → `giftcards`. Neither generates dots. The `camel_to_snake` utility exists (`model.py:67`) but isn't applied — separate gap, doesn't produce reporter's symptom. |
| Maybe `Model.where()` uses a different table-resolution path than `_get_table()`. | Repo grep for `_get_table` — 17 call sites across `model.py` (`save`/`delete`/`find`/`find_by_id`/`select`/`where`/`with_trashed`/etc.) + 2 in `orm/fields.py` for FK descriptors + 2 in `crud/` for AutoCrud — all use the same method. No alternative path. |
| Maybe PG `search_path` modifies how a dotted query resolves. | Empirical test: created `CREATE SCHEMA gift_cards` and set `search_path TO gift_cards, public`. Query `SELECT * FROM gift_cards.gift_card` STILL fails with same error. `search_path` only affects UNQUALIFIED name resolution; dotted schema.table is parsed literally. So even if reporter has a `gift_cards` schema, they need a `gift_card` table inside it. |
| Maybe `TINA4_DATABASE_URL` query string (e.g. `?options=-csearch_path=...`) injects schema setup. | Empirical test: connected with `postgresql://...?options=-csearch_path%3Dgift_cards`. Resulting connection's `search_path` stayed at default `"$user", public`. tina4's PG `connect()` (`postgres.py:186-194`) uses `urlparse` and only extracts host/port/user/password/dbname — URL query string is **ignored**. Could be a feature request (see Adjacent gap 4 below). |
| Maybe PG normalizes both quoted and unquoted dotted SQL to the same error text — so we can't tell the source form from the error alone. | **Confirmed normalization.** All three forms produce byte-identical PG error: `gift_cards.gift_card` (unquoted), `"gift_cards"."gift_card"` (quoted schema-qualified), `"gift_cards.gift_card"` (single-quoted identifier with dot in name). The framework's logged `"sql": ...` payload preserves the SOURCE form though — and reporter's log shows the UNQUOTED form. So we can pin it to `table_name = "gift_cards.gift_card"` (no quotes). |
| Maybe `soft_delete=True` injects `is_deleted = 0` and the reporter doesn't actually have it in their filter. | `ORM.soft_delete` class default is `False` (verified empirically). The auto-injection in `model.py:617` produces `WHERE ({user_filter}) AND (is_deleted = 0 OR is_deleted IS NULL)` — parenthesized and with `OR is_deleted IS NULL`. Reporter's logged SQL has NO parens and NO `OR is_deleted IS NULL` → their `is_deleted = 0` is in their explicit filter, not auto-injected. |
| Maybe reporter's table is actually `gift_card` in a `gift_cards` schema, and the "table exists" claim is correct from their POV. | Still possible — they could have done `CREATE SCHEMA gift_cards` + `CREATE TABLE gift_cards.gift_card`. But PG's error says `does not exist` — definitive. Either their schema/table doesn't exist as named, or they're connected to the wrong DB. Asking reporter to share `\dt+ gift_cards.*` (and ideally `src/orm/GiftCard.py`) is the cleanest next step. |

**Hypothesis stands after thorough disproof.** Framework's contribution to this error is **respecting the user's configuration verbatim**. Not a framework bug at the strict layer.

### Disproof byproduct — recalibration of BH-46 analysis

BH-46 and BH-48 are likely the **same underlying user-side bug** (literal `table_name = "gift_cards.gift_card"`). The BH-46 cascade message was hiding `UndefinedTable: relation "gift_cards.gift_card" does not exist` — NOT `operator does not exist: boolean = integer` as my BH-46 reproduction assumed. My live_repro happened to work because I used `table_name = "gift_cards"` (a sensible default) and built `CREATE TABLE gift_cards`, which triggers boolean=integer on the BH-46 WHERE clause. Reporter's actual trigger was the missing-table error — surfaced only after the v3.13.6 cascade fix.

**This doesn't invalidate the BH-46 fix verification** — the fix solves cascade for ANY trigger error, not specifically boolean=integer. The matrix probe at `pypy/tests/test_issue_46_matrix_probe.py` exercises both error types implicitly (any failing query inside fetch's count probe path). But it calibrates my BH-46 reproduction: I used a different trigger error than what the reporter actually had.

## Adjacent doc/UX gaps the issue surfaces

These aren't the cause of the reporter's specific symptom, but the issue surfaces them. Worth flagging in any upstream reply.

### 1. Ch6 ORM docs never mention schema-qualified table names
`documentation/tina4-book/book-1-python/chapters/06-orm.md` line 125: *"`table_name` — the database table this model maps to. If omitted, the ORM uses the lowercase class name (e.g. `Contact` -> `contact`)."* No guidance on:
- Whether `"public.products"` or `"schema_name.table_name"` syntax is supported
- Whether quoting (`'"schema"."table"'`) works differently
- What the PG `search_path` interaction is
- That setting an invalid dotted name will produce a confusing `relation "x.y" does not exist` error pointing at the framework-generated SQL

For a multi-schema PG deployment (common in enterprise), this is a real gap.

### 2. Default class-name → table-name resolution is naive
`_get_table()` uses `.lower()` only. `GiftCard` → `giftcard` (no snake_case). With `TINA4_ORM_PLURAL_TABLE_NAMES=true`: `GiftCard` → `giftcards`. Most ORM conventions (Rails, Django, SQLAlchemy) generate snake_case: `GiftCard` → `gift_card` or `gift_cards`. The `camel_to_snake` utility exists at `model.py:67` but isn't applied here.

Concrete effect: a user calling `tina4 generate model GiftCard` followed by `tina4 migrate:create "create gift_cards table"` with `CREATE TABLE gift_cards (...)` will hit `relation "giftcard" does not exist` — because the scaffold class with no `table_name` resolves to `giftcard`, not `gift_cards`. They'd need to either rename their migration table or add `table_name = "gift_cards"` manually.

### 3. Error doesn't say which model class generated the bad SQL
`Log.error` at `postgres.py:146-150` emits *"PostgreSQL query failed: ..."* with the SQL but not the model class. Could add `model=cls.__name__` to the structured kwargs at the ORM call site, helping a user with many models find which `table_name` to fix.

### 4. `TINA4_DATABASE_URL` query string is ignored
`PostgreSQLAdapter.connect()` (`postgres.py:186-194`) uses `urlparse` and extracts only host/port/user/password/dbname. The URL's query string (e.g. `?options=-csearch_path=myschema&application_name=tina4`) is dropped. psycopg2 supports passing these as kwargs, but tina4 doesn't forward them. Users wanting a non-public schema default have to set `PGOPTIONS` env var or issue `SET search_path TO ...` manually after connect — neither is documented.

## Potential fix shapes

For Gap 1 (docs):
- Ch6 `table_name` paragraph — one or two lines noting PG schema-qualified syntax is supported as a raw string (`table_name = "myschema.products"`), with quoting examples for case-sensitive identifiers, plus a note that an invalid schema/table produces `UndefinedTable: relation "x.y" does not exist`.
- Or: a small subsection *"Working with PostgreSQL schemas"* in Ch5 Database (since schema choice is engine-specific).

For Gap 2 (resolution):
- Apply `camel_to_snake` (already in same file at `model.py:67`) inside `_get_table()` when `table_name` is unset. `GiftCard` → `gift_card` (default) or `gift_cards` (with pluralization). Behaviour change — would break existing apps relying on the lowercase-only convention. Could be opt-in via `TINA4_ORM_SNAKE_TABLE_NAMES=true`.
- Or document the current behaviour explicitly so users know `GiftCard` → `giftcard` and adjust migrations accordingly.

For Gap 3 (diagnostic):
- One-line addition in the ORM call sites (`select`, `where`, `find`, `find_by_id`, `save`, `delete`) — pass `model=cls.__name__` into `db.fetch()` / `db.execute()` so it reaches `_on_query_error` and lands in the structured log.

## Notes for the upstream reply

Don't reopen #46 or piggyback there. #48 is a separate issue, even if same reporter. The reply should:

1. Acknowledge the error message itself is now visible because of the BH-46 v3.13.6 fix — pre-fix this would have been a cascade.
2. Walk through the empirical reproduction matrix (the byte-identical match at `table_name = "gift_cards.gift_card"`).
3. Ask the reporter to share their `src/orm/GiftCard.py` or equivalent so the literal `table_name` value can be confirmed.
4. Flag the three adjacent gaps as separate doc/UX concerns (lighter touch — they're worth fixing but not blockers).

Don't claim definite root cause without seeing reporter's model file — the byte-match is strong evidence but not proof.

---

## Update 2026-06-10 — OP response + hypothesis revision

OP shared three artifacts:

**1. Model file (`src/orm/GiftCard.py`):**
```python
class GiftCard(ORM):
    table_name = "gift_cards.gift_card"
    gift_card_number = StringField(primary_key=True, required=True)
    # ... other fields including is_deleted = BooleanField(...)
```

Confirms `table_name = "gift_cards.gift_card"` literal — matches my "user typo" hypothesis on the SQL side.

**2. pgAdmin session info (where `SELECT * FROM gift_cards.gift_card` works):**
```
current_user      | current_database
------------------+------------------
staging           | staging
```

**3. `TINA4_DATABASE_URL`:**
```
postgresql://giftcard-service-dev:$(POSTGRES_PWD)@postgres-rw.postgres.svc.cluster.local:5432/giftcard-service-dev
```
- user: `giftcard-service-dev`
- database: `giftcard-service-dev`
- host: `postgres-rw.postgres.svc.cluster.local` (k8s service DNS)
- password: `$(POSTGRES_PWD)` (env/k8s templating placeholder, substituted at runtime)

### Hypothesis broken

Original "user typo" hypothesis: WRONG. `table_name = "gift_cards.gift_card"` is the CORRECT value for OP's setup — the schema/table exists in their `staging` database (confirmed via pgAdmin).

### New observation — connection target mismatch

| | Database | User |
|---|---|---|
| pgAdmin (query works) | `staging` | `staging` |
| Framework (query fails) | `giftcard-service-dev` | `giftcard-service-dev` |

The `gift_cards.gift_card` relation exists in `staging` but apparently not in `giftcard-service-dev` (or the `giftcard-service-dev` user lacks `USAGE` on the schema — PG returns `does not exist` rather than `permission denied` without USAGE).

### Possible interpretations

- **Local-vs-staging environment mismatch.** Most likely. OP may be running their dev app against a local PG seeded from a staging dump, but the schema or `GRANT` statements didn't carry over. Their staging instance has the table; their dev DB doesn't.
- **Missing migration in dev DB.** Schema/table never got migrated to `giftcard-service-dev`.
- **Permission gap on dev DB.** Schema exists but `giftcard-service-dev` user lacks `USAGE`.

### BH-46 recalibration also broken

Earlier "disproof byproduct" claim — that BH-46 and BH-48 are the same underlying user-side bug — is also wrong. They share the BH-46 visibility-fix link (the cascade fix exposed an underlying PG error that was previously hidden), but BH-48's underlying cause is environment-side (DB/connection mismatch), not a `table_name` typo.

**Doesn't change BH-46 fix verification** — fix solves cascade for ANY underlying error class, not specifically boolean=integer OR UndefinedTable. The matrix probe at `pypy/tests/test_issue_46_matrix_probe.py` exercises cascade-hides-cause generically.

### Current state

- OP asked: *"does this issue persist on local and on staging? I assume you are using a staging dump for local?"* — awaiting reply
- 4 adjacent doc/UX gaps from initial investigation still stand (Ch6 schema docs, naive class-name resolution, `Log.error` missing model class, `TINA4_DATABASE_URL` query string ignored)
- No upstream reply posted yet — wait for OP env-confirmation first

### Next-step branches

- **OP says "local only, using staging dump"** → confirmed user/env-side, close BH-48 as not-a-bug + suggest checking dev DB has the schema. Optionally file the 4 doc/UX gaps as separate concerns.
- **OP says "both environments"** → puzzle deepens; permissions or framework/driver-level investigation. Ask `has_schema_privilege` + `has_table_privilege` on dev DB.
- **OP says something unexpected** → continue from there.
