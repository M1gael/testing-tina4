# Does every request store a session?

Ledger row `f-auth-03`. Reported on tina4php 3.13.141: every request, including static
files, 404s and `/health`, creates and stores a session and sets cookies, so session storage
grows with anonymous traffic. Run here on `origin/v3` **3.13.144** of all four ports
(py `37d60025`, php `50b08e76`, rb `228b2cb`, nd `38d68da`), Linux, 2026-10-02.
PHP 8.4.26, Python 3.13.13, Ruby 3.4.10, Node 22.22.2.

## Run it

```
./prove.sh                          # all four, stock worktrees, file backend
PHP_MODE=serve ./prove.sh php       # php under bin/tina4php serve (default: php -S)
PHP_MODE=buffered ./prove.sh php    # serve with output_buffering on: what serve does once tina4-php#259 lands
TINA4_SESSION_BACKEND=database ./prove.sh php python nodejs
TREE_PHP=... TREE_PY=... TREE_RB=... TREE_ND=... ./prove.sh   # any other source tree
```

Each port's app is in its own directory. A client with no cookie sends each request three
times; the store is counted before and after (session files or `tina4_session` rows, and for
php its native PHPSESSID files too) and every `Set-Cookie` name is collected. Then the flows
that must keep working: a write resumes, login (regenerate then set), flash survives exactly
one read, a logged-in form post with `TINA4_CSRF=true` (php), and `$_SESSION` write / login.
Exit 0 all ok, 1 a `BUG` or `BROKEN` cell.

## What stock does (`evidence/stock-3.13.144-linux.txt`)

| port | static, 404, `/health`, untouched route | route that reads | unknown cookie |
|---|---|---|---|
| php (`php -S`) | +1 session, +1 PHPSESSID file, both cookies, each request | same | same |
| php (`serve`) | +1 session, tina4 cookie; since tina4-php#259 (`d3c40d2b`) also +1 PHPSESSID file and cookie (before it the native session never started there: f-auth-01) | same | same |
| nodejs | +1 session file each, cookie (not on the 404) | same | same |
| ruby | nothing | cookie, no file | cookie, no file |
| python | nothing | nothing | cookie, no file |

Same on the database backend (php, python, nodejs; ruby's database backend keeps no session
at all, f-auth-09).

## Mechanism

- php: `Session::save()` writes a session that was minted for the request and never changed
  (`Tina4/Session.php:783-819`: no stored/dirty guard), the router saves after every dispatch
  (`Tina4/Router.php:797`) and sets the cookie whenever the id is not the one sent (`:1430`).
  The router also `session_start()`s PHP's native session on every dispatch (`:731`,
  `:1293`/`:1304`), so PHP creates a PHPSESSID file and cookie for every visitor.
- nodejs: `Session.start()` writes every freshly minted session (`session.ts:618`), and
  `sessionAutoStart` sets the cookie whenever the id is new (`dispatchPipeline.ts:437`).
- ruby: `Request#session` is lazy and `#save` writes nothing for a new unchanged session, but
  the cookie goes out for any instantiated session whose id differs (`dispatch_pipeline.rb:657`).
- python: skips a new empty session, but a request with a cookie the store does not know gets
  the minted replacement's cookie (`core/server.py:2807-2810`), never stored.

The php fix was re-applied to `origin/v3` `d3c40d2b` (#259 merged) and re-run there:
`evidence/php-d3c40d2b-linux.txt`.

## The fix (uncommitted, `~/.cache/tina4-worktrees/fauth03-<port>.fix.patch`)

One rule in all four: a session nothing stored and nothing changed (`isFresh()` /
`is_fresh()` / `fresh?`) writes nothing and gets no cookie. php also defers its native
session when the request brought no PHPSESSID: started with `use_cookies => 0`, kept and its
cookie sent only if `$_SESSION` ends non-empty or a form token was bound to its id
(`Router::keepNativeSession()`, called by Frond's `form_token()`); otherwise destroyed.

After (`evidence/fix-linux.txt`, `evidence/database-backend-stock-and-fix-linux.txt`): every
non-writing cell stores nothing and sets no cookie in every port and mode; writes, resumes,
login, flash, the logged-in form post and `$_SESSION` flows are all ok.

Found while attacking the fix: deferring the native session without the Frond hook broke a
logged-in user's form post under `php -S` (403 `CSRF_INVALID`): php binds `form_token()` to
`session_id()` when a native session is active, and the page that renders the form writes
nothing to `$_SESSION`.

## Not covered

- Apps that key their own data on `session_id()` for a visitor who has written nothing to
  `$_SESSION` (a cart table keyed by it) now see a new id each request. php only.
- An unknown PHPSESSID under `php -S`/FPM still makes PHP create an empty file: there the
  router starts the native session without strict mode (PHP adopts the id). Not this row.
- Redis/valkey/mongo/memcached backends, FPM, uvicorn and puma were not run.
