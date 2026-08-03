# Tina4 Python — AI Context

Tina4 Python v3.13.81. 54 built-in features, zero dependencies.

## Conventions

1. Routes return response() — always response(data) not response.json()
2. GET routes are public, POST/PUT/PATCH/DELETE require auth by default
3. Use @noauth() to make write routes public, @secured() to protect GET routes
4. Decorator order: @noauth/@secured then @description/@tags then @get/@post (route innermost)
5. Every template extends base.twig
6. All schema changes via migrations — never create tables in route code
7. Use built-in features — never install packages for things Tina4 already provides

## Route Pattern

```python
from tina4_python.core.router import get, post, noauth, secured

@get("/api/users")
async def list_users(request, response):
    return response({{"users": []}})

@post("/api/users")
@noauth()
async def create_user(request, response):
    return response({{"created": request.body["name"]}}, 201)
```

## ORM Pattern

```python
from tina4_python.orm import ORM, IntegerField, StringField

class User(ORM):
    table_name = "users"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    email = StringField()
```

## Built-in Features

Router, ORM, Database (SQLite/PostgreSQL/MySQL/MSSQL/Firebird), Frond templates (Twig-compatible), JWT auth, Sessions (File/Redis/Valkey/MongoDB/DB), GraphQL + GraphiQL, WebSocket + Redis backplane, WSDL/SOAP, Queue (File/RabbitMQ/Kafka/MongoDB), HTTP client, Messenger (SMTP/IMAP), FakeData/Seeder, Migrations, SCSS compiler, Swagger/OpenAPI, i18n, Events, Container/DI, HtmlElement, Inline testing, Error overlay, Dev dashboard, Rate limiter, Response cache, Logging, MCP server

## Project Structure

```
src/routes/    — Route handlers (auto-discovered)
src/orm/       — ORM models
src/templates/ — Twig templates
src/app/       — Service classes
src/scss/      — SCSS (auto-compiled)
src/public/    — Static assets
src/seeds/     — Database seeders
migrations/    — SQL migration files
tests/         — pytest tests
```

## Docs

https://tina4.com

<!-- tina4-skills:start -->
## Tina4 Skills

When working on this Tina4 project, these skills give the assistant project-aware behaviour:

- **tina4-developer-python** — Read `.claude/skills/tina4-developer-python/SKILL.md` before building features.
- **tina4-js** — Read `.claude/skills/tina4-js/SKILL.md` for frontend work.
- **tina4-maintainer** — Read `.claude/skills/tina4-maintainer/SKILL.md` for framework-level changes.

If Tina4 behaves differently from what these skills describe, that is a bug in the skill. Tell the developer, then report it at https://tina4.com/report-a-skill (or open an issue on the matching tina4stack/* GitHub repo).

See https://tina4.com for full docs.
<!-- tina4-skills:end -->
