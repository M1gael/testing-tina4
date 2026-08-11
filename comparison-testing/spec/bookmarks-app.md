# Spec — the bookmarks app

The app every framework implements, identically. Written before any app was built, so no
framework's shape influenced the requirements.

It is deliberately the smallest application that still needs the four things a real service
needs: **persistence, authentication, server-rendered HTML, and machine-readable API docs.**
That combination is the point — it is what a hello-world benchmark leaves out, and what
Tina4 claims to give you without extra packages.

## Requirements

### R1 — Schema

A `bookmarks` table with at least:

| Column | Type |
|---|---|
| `id` | integer, primary key, auto-increment |
| `title` | text, required |
| `url` | text, required |

Created by whatever mechanism the framework offers for schema management — a migration, a
schema file, `create_all`. **Not** by hand-running SQL outside the app, and not by shipping
a pre-built database file: creating the schema is part of the work being measured.

SQLite, so no framework is penalised for a server dependency.

### R2 — `GET /api/bookmarks`

Returns every row from the database as a JSON array. Public — no token required.

```json
[{"id": 1, "title": "Tina4", "url": "https://tina4.com"}]
```

Must read from the database. Returning a hardcoded list fails the spec.

### R3 — `POST /api/bookmarks`

Inserts a row and returns it with **201**.

- Requires a valid **JWT** in `Authorization: Bearer <token>`. Without one, or with a
  malformed one: **401**.
- With a valid token but no `url` in the body: **400** and an error message.
- On success: **201** and the created row, including its assigned `id`.

Validation happens after authentication, so a tokenless request with a bad body is 401.

### R4 — `POST /api/login`

Issues a JWT. Public. Body `{"username": "demo", "password": "demo"}` returns
`{"token": "<jwt>"}`. Any other credentials: **401**.

The credentials are hardcoded on purpose. This measures *token issuing and verifying*, not
user management — a full user table would drag ORM breadth into a test that is about
authentication plumbing.

### R5 — `GET /bookmarks`

Server-rendered HTML listing the same rows, through the framework's template engine, using
**template inheritance** — a child template extending a base layout, with the list in a
block. One template file plus one base file.

Inheritance is required because a single flat template understates what every one of these
frameworks actually does.

### R6 — OpenAPI docs

A browsable OpenAPI/Swagger UI documenting R2, R3 and R4, served by the app, at whatever
path the framework uses. The spec document itself must be reachable as JSON.

Hand-written static OpenAPI JSON does not count — it has to be generated from the routes, so
that what is being compared is the framework's ability to produce it.

## Acceptance checks

`scripts/verify-app.sh <port>` runs exactly these. All six must pass before the app is
counted.

| # | Check | Expected |
|---|---|---|
| 1 | `GET /api/bookmarks` | 200, JSON array, rows came from the database |
| 2 | `POST /api/bookmarks` with no token | 401 |
| 3 | `POST /api/login` with `demo`/`demo` | 200 and a token |
| 4 | `POST /api/bookmarks` with that token, no `url` | 400 |
| 5 | `POST /api/bookmarks` with that token and a full body | 201, and the row appears in check 1 on a re-run |
| 6 | OpenAPI JSON reachable, and it mentions `/api/bookmarks` | 200, path present |

The HTML page (R5) is checked by eye — it must render the rows through an inheriting
template. Automating "did inheritance happen" is more trouble than it is worth, but a page
that 404s or shows no rows fails.

## Out of scope

Kept out so the comparison stays about the same thing in every framework:

- Pagination, filtering, sorting
- Refresh tokens, logout, password hashing (the login is a fixture)
- CSRF beyond whatever the framework requires to make R3 work
- Static assets, CSS, client-side JavaScript
- Tests
- Deployment, containers, production servers

If a framework *forces* something extra to make R1–R6 work — Django needs `csrf_exempt` on a
JSON POST, for instance — that is in scope and counts. Being forced into ceremony is exactly
what the measurement is trying to capture.

## Per-framework notes

Recorded as each app is built, so the reasoning behind judgement calls survives:

| Framework | Notes |
|---|---|
| Tina4 | Writes are closed by default, so R2's GET is open and R3 needs no extra work to be protected — but the login route needs `@noauth()`. `Auth.get_token` / `Auth.valid_token` ship with the framework. |
| Flask | Needs a JWT library, an ORM or raw `sqlite3`, and an OpenAPI package. Which combination is chosen, and why, gets recorded here. |
| FastAPI | Generates OpenAPI itself. Needs a JWT library, an ORM, and Jinja2 plus `python-multipart` for templates. |
| Django | Batteries-included but not for JWT or OpenAPI. DRF plus a schema generator plus a JWT package is the conventional route; whether plain Django with hand-rolled JWT is fairer gets decided and recorded. |
