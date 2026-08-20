# Tina4 ResponseCache Cross-Session Replay and Cache-Control Bypass

## Overview

In `tina4-python` 3.13.107, the `ResponseCache` middleware caches responses using only the HTTP method, request URL path, and query parameters as its cache key. Because `ResponseCache._may_store` guards against requests carrying an `Authorization` header but does not check for `Cookie` request headers or `Set-Cookie` response headers, responses containing private user session data are stored in the shared response cache. Furthermore, `ResponseCache._may_store` does not check for standard `Cache-Control: no-store`, `private`, or `no-cache` response directives, causing explicitly uncacheable responses to be stored and replayed across distinct user sessions.

This issue allows authenticated user B to receive private data (such as account numbers and balances) generated for authenticated user A upon requesting the same route. The route is directly reachable using the documented framework middleware syntax (`docs/python/11-caching.md:178`), which instructs users to configure routes with `@get(..., middleware=["ResponseCache:300"])`.

---

## Environment and Versions

- **tina4-python**: `3.13.107`
- **tina4 CLI**: `3.8.77`
- **Date**: 2026-08-20
- **Environment Status**: The local virtual environment (`.venv`) is stock and unpatched. The candidate patch is not permanently applied to this project's venv; `prove.sh` applies the patch temporarily when executed with `--fixed` and restores the original file upon exit, with restoration verified against the stock MD5 checksum.

---

## Root Cause Analysis

The vulnerability originates in `tina4_python/cache/__init__.py`.

### 1. Cache Key Construction (`tina4_python/cache/__init__.py:1396-1403`)

```python
def cache_key(self, request) -> str:
    """The cache key for a request: method + URL + sorted query params."""
    url = getattr(request, "url", "/")
    params = getattr(request, "params", None)
    if params:
        qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"GET:{url}?{qs}"
    return f"GET:{url}"
```

The cache key contains only `method`, `url`, and sorted `params`. It includes no headers, cookies, session identifiers, or user context.

### 2. `ResponseCache._may_store` Fallthrough (`tina4_python/cache/__init__.py:1364-1382`)

```python
@staticmethod
def _may_store(request, response) -> bool:
    if "*" in _vary_fields(response):
        return False
    if _header_value(request, "Authorization") is not None:
        return _shared_cache_allowed(response)
    return True
```

`_may_store` defines three evaluation branches:
1. `if "*" in _vary_fields(response)` (line 1377): Refuses responses where `Vary: *` is present.
2. `if _header_value(request, "Authorization") is not None` (lines 1379–1380): Only checks for the `Authorization` header, permitting storage only if `_shared_cache_allowed(response)` finds `public`, `s-maxage`, or `must-revalidate` in `Cache-Control`.
3. `return True` (line 1381): Default fallthrough.

Requests carrying session cookies (`Cookie: session=...`) do not carry an `Authorization` header. Consequently, they fall straight through to line 1381 (`return True`) and are stored in the shared cache backend.

### 3. Missing Checks for `Cache-Control: no-store`, `private`, and `no-cache`

Searching `tina4_python/cache/__init__.py` reveals zero occurrences of the strings `"no-store"`, `"private"`, or `"no-cache"`. The only directives evaluated are in `_SHARED_CACHE_DIRECTIVES` (`"public"`, `"s-maxage"`, `"must-revalidate"`) on line 1160. Because `_may_store` never inspects whether a response explicitly forbids caching, a route handler emitting `response.header("Cache-Control", "no-store")` is ignored and the response is cached.

### 4. Why `_vary_matches` (`tina4_python/cache/__init__.py:1384-1394`) Does Not Prevent Replay

```python
@staticmethod
def _vary_matches(entry, request) -> bool:
    for field in entry.vary:
        if _header_value(request, field) != entry.vary_values.get(field):
            return False
    return True
```

`_vary_matches` correctly implements RFC 9111 Section 4.1 by verifying that incoming request headers match the headers recorded in `entry.vary`. However, `entry.vary` is populated strictly from the response's `Vary` header via `_vary_fields(response)` (`tina4_python/cache/__init__.py:1185-1190`). Because standard handlers do not emit `Vary: Cookie`, `entry.vary` is empty (`[]`). When `entry.vary` is empty, the loop executes zero iterations and returns `True`, allowing the cached entry to match any subsequent request regardless of differing cookies.

---

## Candidate Patch Analysis (`../.fw17-candidate.patch`)

The candidate patch resolves the vulnerability in `tina4_python/cache/__init__.py` through the following changes:

1. **Directive Token Parsing**: Adds `_cache_control_tokens(carrier)` (lines 128–136) to extract comma-separated `Cache-Control` directives without arguments (e.g., parsing `no-cache="Set-Cookie"` as `no-cache`).
2. **Enforce `no-store`, `private`, and `no-cache`**: In `ResponseCache._may_store`, inspects response directives and immediately returns `False` if any of `{"no-store", "private", "no-cache"}` are present.
3. **Session Cookie Isolation**: In `ResponseCache._may_store`, checks `if _header_value(request, "Cookie") is not None` and `if _header_value(response, "Set-Cookie") is not None`, subjecting them to `_shared_cache_allowed(response)`. A cookie-bearing request or response setting a cookie will not be stored unless explicitly designated `public`, `s-maxage`, or `must-revalidate`.
4. **Regression Tests**: Adds comprehensive test cases (`TestNoStoreAndPrivate` and `TestSessionCookieIsolation` in `tests/test_cache.py`) verifying cookie isolation, `Set-Cookie` protection, `no-store` enforcement, and public cache exceptions.

---

## Reproduction and Proof

The proof script `prove.sh` runs the real Tina4 application server and drives HTTP probes against it.

Note: `prove.sh` stops the server strictly by process ID (`kill "$SERVER_PID"`) rather than pattern matching (such as `pkill -f "$PORT"`), because matching on a command pattern containing the port number would match and terminate the invoking shell script itself.

### Commands

To run against the stock unpatched framework:
```bash
./prove.sh
```

To run with the candidate patch temporarily applied and restored:
```bash
./prove.sh --fixed
```

---

## Stage 1 Output: Stock Framework (`evidence/stage1-stock.txt`)

```
==============================================================
 ResponseCache cross-session replay — STOCK FRAMEWORK (as installed)
 tina4-python 3.13.107   port 17451
==============================================================

1. Two sessions, same URL /account/balance
   ALICE sent Cookie: session=alice_session_token
     -> X-Cache: MISS  {"user":"Alice Smith","account_number":"ACC-9921","balance":"$84,250.00"}
   BOB   sent Cookie: session=bob_session_token
     -> X-Cache: HIT  {"user":"Alice Smith","account_number":"ACC-9921","balance":"$84,250.00"}
  FAIL  BOB must NOT receive Alice's body
        BOB received Alice's account data — cross-user leak

2. Response sets Cache-Control: no-store on /account/no-store
   BOB -> {"user":"Alice Smith","account_number":"ACC-9921","balance":"$84,250.00"}
  FAIL  no-store must prevent storage
        no-store was ignored; Alice's body replayed to BOB

3. Control — Cache-Control: public must still cache (cookies present)
   second request X-Cache: HIT
  PASS  public response still served from cache

4. Control — no cookie at all must still cache
   second request X-Cache: HIT
  PASS  cookieless response still served from cache

==============================================================
 VERDICT: 2 property/properties broken
==============================================================
```

---

## Stage 3 Output: Candidate Fix Applied (`evidence/stage3-fixed.txt`)

```
Applying candidate patch to the installed framework (will be restored).
  patch applied

==============================================================
 ResponseCache cross-session replay — WITH CANDIDATE FIX
 tina4-python 3.13.107   port 17451
==============================================================

1. Two sessions, same URL /account/balance
   ALICE sent Cookie: session=alice_session_token
     -> X-Cache: none  {"user":"Alice Smith","account_number":"ACC-9921","balance":"$84,250.00"}
   BOB   sent Cookie: session=bob_session_token
     -> X-Cache: none  {"user":"Bob Jones","account_number":"ACC-1044","balance":"$12.50"}
  PASS  BOB must NOT receive Alice's body

2. Response sets Cache-Control: no-store on /account/no-store
   BOB -> {"user":"Bob Jones","account_number":"ACC-1044","balance":"$12.50"}
  PASS  no-store must prevent storage

3. Control — Cache-Control: public must still cache (cookies present)
   second request X-Cache: HIT
  PASS  public response still served from cache

4. Control — no cookie at all must still cache
   second request X-Cache: HIT
  PASS  cookieless response still served from cache

==============================================================
 VERDICT: all properties hold
==============================================================
  venv restored from backup
```
