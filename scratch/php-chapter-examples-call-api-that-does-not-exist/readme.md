# php chapter examples call API that does not exist

Ledger `d-misc-02`. Rebuilt and re-run 2026-10-28 against tina4-php origin/v3 b321c1fc; docs
tina4-documentation origin/main 98c70a4, tina4-book origin/main 20b1006. Host Linux, PHP 8.4.
(First built 2026-10-22 on php 30009c17, docs 1828299, book 15ef833; same numbers.)
Fix (uncommitted, branch `docs/dmisc02-fix` cut from those tips): `~/.cache/tina4-worktrees/docfix-dmisc02-{docs,book}`,
patches `docfix-dmisc02-{docs,book}.fix.patch` beside them. `fix.py` here produces the identical tree from a stock tip.
`app/` is a `tina4php init` scaffold; `app/vendor` is a symlink to the php tree's vendor (nothing framework-side lives here).

**Issue and mechanism**, one per piece (`fix.py` numbers them; `SKIP=n` leaves one unfixed):

1. `use Tina4\Database;` (15 hits) and `\Tina4\Database(`/`::` (12 more, ch26/27/34/index): no such class.
   It is `Tina4\Database\Database` (`Database/Database.php:18,41`); no alias. Class-not-found 500.
2. `$request->session["k"]` (ch08, ch16): `Request::$session` is a typed `?Session` (`Request.php:95`), and
   `Session` (`Session.php:34`) has no ArrayAccess: "Cannot use object of type Tina4\Session as array";
   `$request->session = []` is a TypeError. API is `get/set/delete/clear` (`Session.php:253-322`).
3. `$response->file($path, "name.pdf")`: the 2nd parameter is the content type (`Response.php:744`), so the
   download name became the Content-Type header and no Content-Disposition is sent unless `$download` (3rd)
   is true (`:832`). The ch03 routes build `__DIR__ . "/../../..."`, and any `..` segment is refused 403
   (`:772-790`). PHP has no download-name argument (python's `file()` does).
4. ch23 handlers `function ($connection, $event, $data)`: PHP calls `($connection, $payload, $event)`
   (`Server.php:2177,2288,2579`; docblock `Router.php:2833`). ch39 already documents the PHP order.
5. ch21 `$result['status']`: results carry `http_code` (`sendRequest` `Api.php:475`, built at `:570`).
6. ch27 subclasses redeclare `private bool $running`: base has `protected` (`Service.php:50`) -> fatal at declaration.
7. ch15 `TINA4_LOG_OUTPUT=stderr`: accepted values are stdout/file/both, anything else throws
   LogConfigurationError at boot (`Log.php:887`).
8. ch26 `catch (\Tina4\ContainerException)`: no such class; `Container::get()` throws `\RuntimeException`
   "Service not registered: <name>" (`Container.php:86`).

**prove.sh** extracts each block verbatim from DOCS (default origin/main), serves the route blocks through
`tina4php serve` on the scaffold in `app/` (port 7774; refuses a busy port, waits for it to free after stop), runs the script blocks against the tree's autoloader,
speaks WebSocket to `/ws/echo`, and points the ch21 client at the local server instead of jsonplaceholder.
Three static checks back the runtime ones (no `Tina4\Database` left, no old-order handler, no `'status'` read).

    ./prove.sh                                                     # stock docs: VERDICT ok=1 bad=19, exit 1
    DOCS=~/.cache/tina4-worktrees/docfix-dmisc02-docs/docs/php ./prove.sh               # ok=20 bad=0
    DOCS=~/.cache/tina4-worktrees/docfix-dmisc02-book/book-2-php/chapters ./prove.sh    # ok=20 bad=0

Per-piece gating (`SKIP=n python3 fix.py <stock copy>`, then prove; docs and book identical): 1 -> 3 FAIL (db x2, container), 2 -> 2, 3 -> 4, 4 -> 2,
5 -> 3, 6 -> 4, 7 -> 1, 8 -> 1. Docs site builds (`tina4press build .`, 283 pages).

**Not fixed here:** `36-releases.md:5328-5329` still shows `new \Tina4\Database(...)` (release notes left as
history; still there on 98c70a4). ch21 has more mismatches than the status key: payload as "fourth argument" (it is the third; the
fourth is the content-type string), query params as the third, `addCustomHeaders()` (is `addHeaders`),
`setUsernamePassword()` (is `setBasicAuth`), per-call timeout options. ch05 §3 promises `{"answer": 2}`;
it returns `[{"answer": 2}]`. Still true on docs 98c70a4 / rb 74aa1f5 / nd b447252 (read): same `file($path, "name")` mistake in ruby ch03 (`response.rb:192` (ArgumentError: `content_type:` is a
keyword, inferred) and nodejs ch03 (`response.ts:379`, 2nd arg is an options object; name silently dropped, inferred); python is right.
