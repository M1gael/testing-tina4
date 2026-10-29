# CSRF: docs say on by default, all four ports have it off

Ledger `d-auth-02`. Run 2026-10-28 on stock tina4-python efa826a3, tina4-php b321c1fc, tina4-ruby 74aa1f5,
tina4-nodejs b447252 (origin/v3); docs tina4-documentation origin/main 98c70a4, tina4-book origin/main 20b1006.
Framework trees: ~/.cache/tina4-worktrees/docfix-dauth02-stock-{python,php}, docfix-stock-{ruby,nodejs} (nodejs
`packages/core` dist rebuilt at that commit). Fix (uncommitted): ~/.cache/tina4-worktrees/docfix-dauth02-{docs,book},
branch docs/dauth02-fix cut from those origin/main tips, patches beside them as `*.fix.patch`.

**Issue.** ch10 of all four ports says "CSRF protection is on by default", its checklist says
"`TINA4_CSRF=true` (the default)", its intro lists CSRF among the secure defaults, and its "Disabling CSRF
Globally" section treats `TINA4_CSRF=false` as the opt-out. ch33 for python and php, general/04 and php ch37
also give the default as on. The code has it off in every port. ruby and nodejs ch33 already say `false`.

**Intended, not a code fault.** The middleware is attached only when `TINA4_CSRF` is truthy, and each port
says so in its docblocks ("CSRF is OFF by default"). This was the deliberate 3.13.98 change (`32494958`,
CHANGELOG "`TINA4_CSRF=true` now actually attaches the CSRF middleware"). So the docs are what is wrong.

**Mechanism.** If `TINA4_CSRF` is not one of true/1/yes/on, nothing registers `CsrfMiddleware`:
- py `tina4_python/core/middleware.py:842-843` (`attach_csrf_from_env`), called from `core/server.py:3082`
- php `Tina4/Middleware/CsrfMiddleware.php:223-224` (`attachFromEnv`), called from `Tina4/App.php:617`
- rb `lib/tina4/middleware.rb:770-771` (`attach_from_env`), called from `lib/tina4.rb:500`
- nd `packages/core/src/middleware.ts:1225-1228` (`attachCsrfFromEnv`), called from `packages/core/src/server.ts:2252`

**prove.sh** runs each port's real server with a logged-in browser: the identity token sits in the session, there is
no Bearer, the form is each ch10's "The Template" block verbatim, and the route is a default write route. It posts
once with no token and once with the rendered form token, first with `TINA4_CSRF` unset and then with `TINA4_CSRF=true`.
The enabled run must give 403 then 200, which shows the harness actually reaches CSRF. Every page that states the
default is then checked against the observed default; ch10 must state the observed default, not just stop claiming "on".
Ports 7541-7548 (`PORT=` moves the base); a busy port is refused. `DOCS=<docs dir> BOOK=<book root> ./prove.sh`;
with neither set it uses origin/main. Exit 0 docs agree, 1 docs wrong, 2 harness broken.

```
py   TINA4_CSRF unset: no token 200, form token 200 | TINA4_CSRF=true: no token 403, form token 200 | noauth, CSRF on, no token: 200
php  (same)   rb (same)
nd   (same, except)                                                                              | noauth, CSRF on, no token: 403
observed default: py=off php=off rb=off nd=off
stock  VERDICT docs-wrong=24 (wrong lines 44)   exit 1
fixed  VERDICT docs-wrong=0  (wrong lines 0)    exit 0
```

`apply-fix.py <root> [piece...]` applies the fix to either tree; on the tips it reproduces the held patches byte for
byte. Each piece left out on its own turns the proof red: intro 8, middleware 16, toggle 8, checklist 8, ch33 4,
general 2, php37 2. tina4press build of the fixed docs: 283 pages, exit 0.

**Not fixed here (separate):**
- The ch10 exercise solution in all four ports says "The middleware validates the token" on a no-auth route. In py,
  php and rb no-auth skips CSRF (the run's no-token POST to the no-auth route is 200 with CSRF on; py
  `middleware.py:713-715`, php `CsrfMiddleware.php:74-86`), so the sentence is wrong there.
- nodejs is the reverse, and that is a code fault: its docblock says no-auth routes skip CSRF
  (`middleware.ts:1119`), but `csrfRouteSkips` (`middleware.ts:1075-1078`) reads `req._route ?? req.route`, which
  nothing in `packages/core/src` sets (`runMatchedRoute`, `server.ts:1177-1180`, sets only `req.params`). A
  `Router.post(...).noAuth()` route answers 403 CSRF_INVALID to a tokenless POST when CSRF is on.
- php ch33 names `_csrf` / `X-CSRF-Token`, but the code reads `formToken` / `X-Form-Token` (`CsrfMiddleware.php:129-138`).
- python ch36 (`36-releases.md:5229`) has "CSRF is on by default in v3.9.1+" in an old release's notes; history, left alone.
