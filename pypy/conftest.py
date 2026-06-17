# pytest conftest — runs before any test is collected.
#
# Why this file exists:
#
# 1. .env loading. The Tina4 framework only reads `.env` during `tina4 serve`
#    (via run()). Under pytest, .env is never loaded, so TINA4_DATABASE_URL is
#    absent from os.environ and every ORM call raises "No database bound". The
#    ORM reads TINA4_DATABASE_URL from os.environ lazily, so loading .env here
#    (before any test imports a model) binds the whole suite to the configured
#    database — currently postgresql://...tina4testingdb. setdefault is used so a
#    test that explicitly sets its own URL (e.g. the BH-46 PG fixtures) still wins.
#
# 2. Route registration. The framework auto-loads `src/routes/*.py` only during
#    run(). Under pytest, Router.match() has zero user routes registered, so a
#    test hitting `/api/products` gets a 404 even though the route file exists.
#    Importing every route module here registers the @get/@post/etc. decorators.

import os

_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _fh:
        for _line in _fh:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _key, _val = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _val.strip())

import importlib
import pkgutil
import src.routes

for _, name, _ in pkgutil.iter_modules(src.routes.__path__, prefix="src.routes."):
    importlib.import_module(name)
