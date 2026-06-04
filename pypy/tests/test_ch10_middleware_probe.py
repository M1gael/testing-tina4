# ch10 sections 3 + 4 — middleware dispatcher probe
# Empirically demonstrates PY-10-01: function-based middleware is documented as
# one of two supported styles (Ch10 §3), but the framework dispatcher only
# handles class-based. Function bodies never execute.
#
# This probe invokes `_run_before_middleware` directly (skipping TestClient,
# which doesn't run middleware at all) so the dispatcher behaviour is isolated.
# Each middleware appends to a list when it runs; the list tells the truth.

from tina4_python.test import Test, assert_in, assert_not_in, assert_equal, assert_true
from tina4_python.core.server import _run_before_middleware
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

    def test_decorated_post_route_silently_unauthenticated(self):
        """PY-10-02: applying @middleware() to the same kind of route flips
        auth_required to False — even though the middleware itself does nothing
        (and per PY-10-01 wouldn't even execute if it tried). The route is now
        wide open with no warning in the docs."""
        route = decorated_post._route_ref._route
        assert_equal(route.get("auth_required"), False,
                     "PY-10-02: @middleware() silently disabled the auth gate")


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

    def test_docs_pattern_capital_A_returns_None(self):
        """Chapter examples (§10 line 546, §12 line 664/677) use mixed-case keys.
        These silently return None."""
        req = _make_request_with_auth_header()
        result = req.headers.get("Authorization")
        assert_equal(result, None,
                     "PY-10-03: capital-A 'Authorization' returns None because "
                     "the dict is lowercase-keyed")

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
