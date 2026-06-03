# pytest conftest — runs before any test is collected.
#
# Why this file exists: the Tina4 framework only auto-loads `src/routes/*.py`
# during `tina4 serve` (via run()). When pytest runs the test client directly,
# Router.match() has zero user-defined routes registered — so any test hitting
# `/api/products` (or similar) gets a 404 even though the route file exists.
#
# This conftest imports every route module so the @get/@post/etc. decorators
# register the routes with Router before tests start.

import importlib
import pkgutil
import src.routes

for _, name, _ in pkgutil.iter_modules(src.routes.__path__, prefix="src.routes."):
    importlib.import_module(name)
