# Issue: `@cached` Decorator Never Attaches Response Cache

## Summary

The `@cached` decorator provided by `tina4_python.core.router` is completely inert. Decorating a route with `@cached(max_age=120)` (in either the documented `@cached`-above-`@get` order or the reversed order) does not attach the `ResponseCache` middleware, does not populate any `X-Cache` headers, and does not cache HTTP responses. Every incoming request executes the route handler from scratch.

While the underlying `ResponseCache` middleware and direct string/class attachment work as expected, all declarative caching surfaces (`@cached`, `RouteRef.cache()`, and `route["cached"]`) write state that is never read during request dispatch.

---

## Published Contract Broken

The official Tina4 documentation advertises `@cached` as a primary method for attaching response caching:

From `docs/python/11-caching.md` (lines 216–240):

```python
### Three ways to attach it

The string form (no import) and the class form both work.

from tina4_python.core.router import get, middleware, cached
from tina4_python.cache import ResponseCache

# 1. String in the middleware list (TTL after the colon)
@get("/api/a", middleware=["ResponseCache:300"])
async def route_a(request, response):
    return response({"ok": True})

# 2. The @middleware decorator with the class (uses TINA4_CACHE_TTL, default 60s)
@middleware(ResponseCache)
@get("/api/b")
async def route_b(request, response):
    return response({"ok": True})

# 3. The @cached decorator for a per-route TTL override
@cached(max_age=120)
@get("/api/c")
async def route_c(request, response):
    return response({"ok": True})
```

From `docs/python/index.md` (lines 551–560):

```python
### Response Cache <a href="#response-cache" id="response-cache"></a>

from tina4_python.core.router import get, cached

@cached(max_age=120)
@get("/api/products")
async def products(request, response):
    return response(expensive_query())
```

Of the three documented attach methods, ways #1 and #2 work, while way #3 (`@cached`) silently does nothing.

---

## Reproduction

### Environment & Versions
- **Date**: 2026-08-20
- **tina4-python**: `3.13.107`
- **tina4 CLI**: `3.8.77`
- **Python**: `3.13.5`

### Test Routes (`src/routes/timing.py`)

```python
import time
from tina4_python.core.router import get, cached

# 1. Documented order: @cached above @get
@cached(max_age=120)
@get("/docs-order")
async def docs_order(request, response):
    return response({"t": time.time()})

# 2. Reversed order
@get("/reversed-order")
@cached(max_age=120)
async def reversed_order(request, response):
    return response({"t": time.time()})

# 3. Control: string middleware form (works)
@get("/middleware-form", middleware=["ResponseCache:120"])
async def middleware_form(request, response):
    return response({"t": time.time()})

# 4. Control: undecorated (no caching)
@get("/undecorated")
async def undecorated(request, response):
    return response({"t": time.time()})
```

### Running the Proof Script

```bash
./prove.sh
```

### Captured Output (`evidence/stage1-stock.txt`)

```
==============================================================
 @cached decorator attach probe — STOCK FRAMEWORK
 tina4-python 3.13.107   port 17453
==============================================================

1. Route /docs-order — @cached(max_age=120) above @get (documented order)
   first  request -> X-Cache: none  body: {"t":1787231107.0286343}
   second request -> X-Cache: none  body: {"t":1787231107.1617749}
  FAIL  @cached above @get should serve second response from cache (X-Cache: HIT)
        expected X-Cache: HIT, got 'none' (body changed: yes)

2. Route /reversed-order — @get above @cached(max_age=120) (reversed order)
   first  request -> X-Cache: none  body: {"t":1787231107.192382}
   second request -> X-Cache: none  body: {"t":1787231107.3268237}
  FAIL  @get above @cached should serve second response from cache (X-Cache: HIT)
        expected X-Cache: HIT, got 'none' (body changed: unity/different)

3. Control — /middleware-form with middleware=["ResponseCache:120"]
   first  request -> X-Cache: MISS  body: {"t":1787231107.3591568}
   second request -> X-Cache: HIT  body: {"t":1787231107.3591568}
  PASS  middleware=["ResponseCache:120"] serves second response from cache (X-Cache: HIT)

4. Control — /undecorated (no cache requested)
   first  request -> X-Cache: none  body: {"t":1787231107.5121722}
   second request -> X-Cache: none  body: {"t":1787231107.6419332}
  PASS  undecorated route is not cached (no X-Cache, body updates)

==============================================================
 VERDICT: 2 property/properties broken
==============================================================
```

Exit code: `2` (non-zero due to the two broken `@cached` properties).

---

## Root Cause & Mechanism

Inspection of `tina4_python` package source files reveals why the decorator is dead:

### 1. The `@cached` Decorator Definition
In `tina4_python/core/router.py` (lines 1036–1042):

```python
def cached(max_age: int = 60):
    """Cache the response of this route."""
    def decorator(fn):
        fn._cached = True
        fn._cache_max_age = max_age
        return fn
    return decorator
```

`@cached` stamps `fn._cached = True` and `fn._cache_max_age = max_age` on the handler function. It does not append `ResponseCache` to `fn._middleware` or update `fn._route_ref._route["middleware"]`.

### 2. `_cached` Is Never Read on Dispatch
A codebase search across `tina4_python` shows that `fn._cached` is never checked anywhere in `core/router.py`, `core/server.py`, `core/middleware.py`, or any dispatch pipeline.

### 3. `_cache_max_age` IS Read (TTL Plumbing Exists)
In `tina4_python/cache/__init__.py` (lines 1464–1481):

```python
    @staticmethod
    def _get_route_ttl(request) -> int | None:
        """The per-route TTL from ``@cached(max_age=N)``, or None.

        Read off the matched handler, which the dispatcher attaches to the
        request as ``_handler``. ``@cached`` stamps ``_cache_max_age`` on the
        function...
        """
        handler = getattr(request, "_handler", None)
        max_age = getattr(handler, "_cache_max_age", None)
        if max_age is not None:
            return int(max_age)
        meta = getattr(request, "_route_meta", None)
        if meta and "cache_max_age" in meta:
            return int(meta["cache_max_age"])
        return None
```

This indicates that the TTL consumption logic is already implemented inside `ResponseCache`. If `ResponseCache` middleware is executed, it successfully reads `handler._cache_max_age`. However, because `@cached` never attaches `ResponseCache` to the route's middleware chain, `ResponseCache` is never invoked.

### 4. Three Dead Attach Surfaces
There are three distinct dead caching surfaces in `tina4_python/core/router.py`:
1. **The `@cached` decorator** (`core/router.py:1039`): Sets `fn._cached = True`, which is never read.
2. **`RouteRef.cache()`** (`core/router.py:71–74`):
   ```python
   def cache(self):
       """Mark this route as cacheable."""
       self._route["cached"] = True
       return self
   ```
   Sets `self._route["cached"] = True`.
3. **Route dictionary key `cached`** (`core/router.py:424`):
   ```python
   "cached": options.get("cached", False),
   ```
   Initialized in `Router.add`, but `route["cached"]` is never inspected anywhere in the dispatch pipeline.

---

## Important Precedence / Sequencing Note

Fixing `@cached` without first fixing the response-cache session leak (documented and proven in `../response-cache-replays-across-sessions`) would automatically widen that cross-session data leak to every route using `@cached`. Any fix for decorator attachment must be sequenced after or alongside the response-cache isolation fix.

---

## Status

**Stages 1 and 2 complete.**
- Stage 1: Issue reproduced over real HTTP on stock 3.13.107.
- Stage 2: Mechanism and dead surfaces identified with exact file and line references.
- Stage 3: **No candidate fix exists yet.** Outstanding until a patch is developed.
