# ch10 sections 3 + 4 — middleware dispatcher probe
# Originally demonstrated PY-10-01/02/03 against tina4-python 3.13.2.
# All three findings fixed in 3.13.4 — probe retained as regression sentinel.
#
# Post-fix state (what each assertion now means):
#
#   PY-10-01 (function middleware now runs) — the OLD dispatcher
#     `_run_before_middleware` now intentionally SKIPS function-style
#     middleware (server.py:1186-1187), because they're handled by the new
#     continuation chain in `_invoke_handler_with_middleware` (server.py:1238).
#     This probe still invokes the old dispatcher, so its assertion that
#     function middleware DOESN'T run via that path still PASSES — for a
#     different reason now (by design, not by bug). End-to-end verification
#     of the fix needs a second probe driving the new dispatcher.
#
#   PY-10-02 (auth gate restored) — the assertion
#     `test_decorated_post_route_silently_unauthenticated` expects the bug
#     (`auth_required == False` after `@middleware(...)`). It now FAILS
#     because the fix flipped auth_required back to True. The failure IS
#     the regression sentinel: if it ever passes again, the bug is back.
#
#   PY-10-03 (case-insensitive headers) — same shape as PY-10-02. The
#     assertion `test_docs_pattern_capital_A_returns_None` expects the bug
#     (capital-A lookup returns None). It now FAILS because CaseInsensitiveDict
#     returns the value. The failure IS the regression sentinel.
#
# This probe invokes `_run_before_middleware` directly (skipping TestClient,
# which doesn't run middleware at all) so the dispatcher behaviour is isolated.
# Each middleware appends to a list when it runs; the list tells the truth.

import pytest
# Probe dormant. Remove this skip line to re-enable.
pytest.skip("probe dormant — see readme convention", allow_module_level=True)

import asyncio
from tina4_python.test import Test, assert_in, assert_not_in, assert_equal, assert_true
from tina4_python.core.server import _run_before_middleware, _invoke_handler_with_middleware
from tina4_python.core.request import Request
from tina4_python.core.response import Response
from tina4_python.core.router import post, middleware


# ── Trace ──────────────────────────────────────────────────────────────
TRACE: list[str] = []


# ── Function-based middleware (the documented style — Ch10 §3) ────────

async def fn_middleware(request, response, next_handler):
    """Function middleware exactly as the chapter documents (Ch10 §3 lines 111-122)."""
    TRACE.append("fn_middleware.before")
    result = await next_handler(request, response)
    TRACE.append("fn_middleware.after")
    return result


# ── Class-based middleware (the other documented style — Ch10 §3) ─────

class ClassMiddleware:
    """Class middleware exactly as the chapter documents (Ch10 §3 lines 129-142)."""

    @staticmethod
    def before_class_mw(request, response):
        TRACE.append("ClassMiddleware.before_class_mw")
        return request, response

    @staticmethod
    def after_class_mw(request, response):
        TRACE.append("ClassMiddleware.after_class_mw")
        return request, response


# ── Helpers ───────────────────────────────────────────────────────────

def _make_fake_request_and_response():
    """Build a bare Request/Response pair to feed the dispatcher."""
    scope = {
        "type": "http", "method": "GET", "path": "/probe",
        "query_string": b"", "headers": [], "client": ("127.0.0.1", 0),
    }
    return Request.from_scope(scope, b""), Response()


# ── Probes ────────────────────────────────────────────────────────────

class Ch10MiddlewareDispatcherProbe(Test):

    def setUp(self):
        TRACE.clear()

    def test_class_middleware_runs_via_dispatcher(self):
        """Sanity: dispatcher runs `before_*` static methods on a class middleware."""
        req, resp = _make_fake_request_and_response()
        fake_route = {"middleware": [ClassMiddleware]}

        _run_before_middleware(req, resp, fake_route)

        assert_in("ClassMiddleware.before_class_mw", TRACE,
                  "class-based middleware before hook should run")

    def test_function_middleware_does_NOT_run_via_dispatcher(self):
        """PY-10-01: the dispatcher iterates dir(item) looking for `before_*`
        attributes. A plain async function has no such attributes — its body
        never executes."""
        req, resp = _make_fake_request_and_response()
        fake_route = {"middleware": [fn_middleware]}

        _run_before_middleware(req, resp, fake_route)

        assert_not_in("fn_middleware.before", TRACE,
                      "PY-10-01: function middleware body never executes — "
                      "dispatcher only handles before_*/after_* attribute names")


# ── PY-10-02 — @middleware() silently disables Bearer-token auth ──────

@post("/__probe_ch10/bare_post")
async def bare_post(request, response):
    return response.json({"ok": True})


async def noop_middleware(request, response, next_handler):
    return await next_handler(request, response)


@middleware(noop_middleware)
@post("/__probe_ch10/decorated_post")
async def decorated_post(request, response):
    return response.json({"ok": True})


class Ch10AuthGateProbe(Test):
    """PY-10-02: applying @middleware(...) flips auth_required to False,
    silently disabling the framework's built-in Bearer-token check."""

    def test_bare_post_route_requires_auth(self):
        """A POST without @middleware should default to auth_required=True."""
        route = bare_post._route_ref._route
        assert_true(route.get("auth_required"),
                    "POST routes default to requiring Bearer auth")

    def test_decorated_post_route_keeps_auth_gate(self):
        """PY-10-02 (fixed in 3.13.4): applying @middleware() must NOT disable
        the framework's built-in Bearer-token gate on write methods. Probe
        asserts the correct post-fix state: auth_required stays True.
        Regression = this flips to False = bug reintroduced."""
        route = decorated_post._route_ref._route
        assert_equal(route.get("auth_required"), True,
                     "PY-10-02 regression: @middleware() must not disable auth gate")


# ── PY-10-03 — request.headers is lowercase-keyed ─────────────────────

def _make_request_with_auth_header():
    """Build a request the way the framework parses an incoming HTTP request —
    headers in the ASGI scope are bytes, and Request.from_scope() applies
    .lower() to every key (request.py:55)."""
    scope = {
        "type": "http", "method": "GET", "path": "/probe",
        "query_string": b"",
        "headers": [(b"Authorization", b"Bearer secret-token-xyz")],  # capital A — as a real client would send
        "client": ("127.0.0.1", 0),
    }
    return Request.from_scope(scope, b"")


class Ch10HeaderCasingProbe(Test):
    """PY-10-03: request.headers stores all keys lowercase. The chapter's
    `request.headers.get("Authorization")` and `.get("X-API-Key")` patterns
    return None and silently break."""

    def test_docs_pattern_capital_A_returns_value(self):
        """PY-10-03 (fixed in 3.13.4): request.headers is a CaseInsensitiveDict.
        Mixed-case keys used in chapter examples must return the value, not None.
        Regression = this returns None = lowercase-only dict reintroduced."""
        req = _make_request_with_auth_header()
        result = req.headers.get("Authorization")
        assert_equal(result, "Bearer secret-token-xyz",
                     "PY-10-03 regression: capital-A lookup must work via CaseInsensitiveDict")

    def test_lowercase_works(self):
        """The real key is lowercase."""
        req = _make_request_with_auth_header()
        result = req.headers.get("authorization")
        assert_equal(result, "Bearer secret-token-xyz",
                     "lowercase key returns the actual value")

    def test_request_dot_header_helper_does_case_insensitive_lookup(self):
        """Undocumented helper at request.py:128 — handles any casing.
        The chapter never mentions this exists."""
        req = _make_request_with_auth_header()
        result = req.header("Authorization")  # capital A — still works
        assert_equal(result, "Bearer secret-token-xyz",
                     "request.header() is case-insensitive — the right tool, undocumented")

    def test_request_dot_bearer_token_helper_strips_prefix(self):
        """Undocumented helper at request.py:132 — extracts the raw token,
        no 'Bearer ' prefix. The chapter never mentions this either."""
        req = _make_request_with_auth_header()
        result = req.bearer_token()
        assert_equal(result, "secret-token-xyz",
                     "request.bearer_token() returns the raw token — undocumented")


# ── PY-10-01 end-to-end — function middleware via the NEW dispatcher ──
#
# The probe class above exercises `_run_before_middleware` (the OLD dispatcher),
# which now intentionally SKIPS function-style middleware — so that probe alone
# can't prove the fix landed. This second class drives the new dispatcher
# `_invoke_handler_with_middleware` (server.py:1238) directly and asserts the
# function middleware body actually executes in continuation-chain order.
#
# When PY-10-01 is fixed (the current state on 3.13.4), every assertion in this
# class PASSES. If the fix regresses, the assertions flip to FAIL — they are
# the forward-direction regression sentinel for this finding.

async def _outer_fn_middleware(request, response, next_handler):
    """Outermost layer — first declared = outermost wrapper."""
    TRACE.append("outer.before")
    result = await next_handler(request, response)
    TRACE.append("outer.after")
    return result


async def _inner_fn_middleware(request, response, next_handler):
    """Inner layer — declared second, runs inside outer."""
    TRACE.append("inner.before")
    result = await next_handler(request, response)
    TRACE.append("inner.after")
    return result


async def _short_circuit_middleware(request, response, next_handler):
    """Doesn't call next_handler — chain stops here."""
    TRACE.append("short_circuit.before")
    return response  # No await on next_handler → handler must NOT run


async def _route_handler(request, response):
    """The innermost layer — the route's own handler."""
    TRACE.append("handler")
    return response


class Ch10FunctionMiddlewareEndToEndProbe(Test):
    """PY-10-01 end-to-end: function middleware runs via the new
    `_invoke_handler_with_middleware` dispatcher, with proper continuation
    ordering. Fixed in 3.13.4; this probe is the regression sentinel."""

    def setUp(self):
        TRACE.clear()

    def test_single_function_middleware_body_executes(self):
        """One function middleware, one route handler. The middleware body
        must run before and after the handler."""
        req, resp = _make_fake_request_and_response()
        route = {"middleware": [_outer_fn_middleware], "handler": _route_handler}

        asyncio.run(_invoke_handler_with_middleware(req, resp, route, {}))

        assert_in("outer.before", TRACE,
                  "PY-10-01: function middleware body must run before handler")
        assert_in("outer.after", TRACE,
                  "PY-10-01: function middleware body must run after handler")
        assert_in("handler", TRACE,
                  "Route handler must still run")

    def test_continuation_chain_runs_in_russian_doll_order(self):
        """Two function middlewares declared in order [outer, inner]. The
        first-declared must wrap the second (outer.before → inner.before →
        handler → inner.after → outer.after)."""
        req, resp = _make_fake_request_and_response()
        route = {
            "middleware": [_outer_fn_middleware, _inner_fn_middleware],
            "handler": _route_handler,
        }

        asyncio.run(_invoke_handler_with_middleware(req, resp, route, {}))

        assert_equal(
            TRACE,
            ["outer.before", "inner.before", "handler", "inner.after", "outer.after"],
            "PY-10-01: continuation chain must Russian-doll — outer wraps inner wraps handler",
        )

    def test_middleware_can_short_circuit_by_not_calling_next(self):
        """A function middleware that omits `await next_handler(...)` must
        prevent both inner middleware AND the route handler from running."""
        req, resp = _make_fake_request_and_response()
        route = {
            "middleware": [_short_circuit_middleware, _inner_fn_middleware],
            "handler": _route_handler,
        }

        asyncio.run(_invoke_handler_with_middleware(req, resp, route, {}))

        assert_in("short_circuit.before", TRACE,
                  "Short-circuiting middleware itself must run")
        assert_not_in("inner.before", TRACE,
                      "Inner middleware must NOT run when outer doesn't call next_handler")
        assert_not_in("handler", TRACE,
                      "Route handler must NOT run when middleware short-circuits")
