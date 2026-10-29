# Do the read-only side claims hold? (2026-10-28)

Six claims that earlier passes had established only by reading source. Each one is re-checked here by running it.
This directory changes nothing in the docs or the frameworks. It corresponds to existing ledger rows and adds no row of its own.

Pinned: tina4-ruby `origin/v3` 74aa1f5, tina4-nodejs `origin/v3` b447252, tina4-php `origin/v3` b321c1fc,
tina4-python `origin/v3` efa826a3 (used only for claim 6), docs tina4-documentation `origin/main` 98c70a4.

## Run

```bash
/var/home/work/gitdir/testing-tina4/scratch/do-the-read-only-side-claims-hold-on-2026-10-28/run-all.sh
```

It prints one line per claim. PASS means the claim as stated holds. FAIL means it does not. BROKEN means a control
did not give its required answer. Exit codes: 0 means all PASS, 1 means any FAIL, 2 means any BROKEN. A run takes about 12s.
It uses ports 7650-7654 and 7660-7667, refuses a busy port, kills every process it starts and waits for each port to free.
Each app is copied to a temp dir before it runs, so the framework's scaffolding never lands here. `HOME` is a temp dir for every run.

Setup, once. The worktrees are detached at the pinned shas, and deps are hardlinked from the tinaforks checkouts:

```bash
W=~/.cache/tina4-worktrees; F=~/gitdir/tinaforks
for r in ruby nodejs php python; do git -C $F/tina4-$r worktree add --detach $W/side1028-$r origin/v3; done
cp -al $F/tina4-nodejs/node_modules $W/side1028-nodejs/ && (cd $W/side1028-nodejs && HOME=$(mktemp -d) npm run build)
cp -al $F/tina4-php/vendor $W/side1028-php/      # autoload/require identical between 7f1f1dc3 and b321c1fc
```

Python runs with `PYTHONPATH=side1028-python` on `tinaforks/tina4-python/.venv/bin/python`.

## Claims and what the run showed

Every claim pairs the doc's call with a control: the correct call, which must succeed, so the instrument could have
given the other answer.

1. **ch03 `file(path, "name")`, ruby and nodejs**: HOLDS.
   - **ruby:** the doc's call returns 500, `wrong number of arguments (given 2, expected 1)` at `response.rb:192`.
     The second positional argument is rejected because the remaining parameters are keyword-only.
   - **nodejs:** the doc's call returns 200 inline with no `Content-Disposition`, and the name is silently dropped (`response.ts:379`).
   - **Controls:** `file(p, download: true)` and `file(p, {download: true})` both give 200 with `attachment; filename="report.pdf"`.
   - **Side finding:** neither port has a custom-filename option at all. The attachment name is always the file's basename.
2. **nodejs `Database.getConnection()`**: HOLDS.
   - Two calls return different `Database` objects, and `getAdapter()` changes between them.
   - The second connection cannot see a table made through the first (`sqlite::memory:`).
   - **Control:** two plain `getAdapter()` calls return the same object.
   - Cites unchanged: `database.ts:1903` and `initDatabase` at `:1928`, which calls `setAdapter` at `:1951` and `:1984`.
3. **nodejs `createTable()` before any instance**: HOLDS.
   - The columns come out as `id,authorId,title`. `create()` then logs `table posts has no column named author_id`,
     returns an instance with `id=undefined` (no throw), and no row is written.
   - **Control:** constructing one instance first gives `author_id`, and the save writes 1 row. Mechanism at `baseModel.ts:264-270`.
4. **php ch21 and ch05 §3**: HOLDS, all six parts.
   - **Payload as the 4th argument:** TypeError, because arg 4 is `$contentType` (`Api.php:475`).
   - **"Query params" as the 3rd argument:** they are sent as a JSON body, with an empty query string. `get($path, $params)` is what builds the query.
   - **`addCustomHeaders()` and `setUsernamePassword()`:** both are undefined methods. The real ones are `addHeaders` (`:216`)
     and `setBasicAuth` (`:232`).
   - **Per-call timeout:** the doc's form is a TypeError. With a valid 4th argument, a 5th `['timeout'=>1]` is silently
     ignored: the call returns 200 after 3s against a 3s endpoint. The constructor `timeout: 1` does cut it at 1s.
   - **ch05 §3:** with the class named by its real namespace, `fetch` returns `[{"answer":2}]`. `fetchOne` gives the
     `{"answer":2}` the doc prints.
   - **Side finding:** the doc's own `use Tina4\Database;` returns 500 with `Class "Tina4\Database" not found`. The class is
     `Tina4\Database\Database`, and that import appears 7 times in php ch05 and on 5 more php pages.
   - The controls need `allowHosts: ['127.0.0.1']`, because the SSRF guard blocks loopback by default.
5. **php ch33 CSRF field names**: HOLDS.
   - The setup has CSRF on, a logged-in session, and a framework-minted form token.
   - With no token: 403. With `formToken` in the body or the `X-Form-Token` header: 200.
   - With `_csrf` in the body or the `X-CSRF-Token` header, the names ch33 documents (line 95): 403.
   - Cite unchanged: `CsrfMiddleware.php:127-138`.
6. **nodejs no-auth route still CSRF-checked**: HOLDS.
   - **Unit:** the built `CsrfMiddleware.beforeCsrf` (which calls `csrfRouteSkips`, `middleware.ts:1075-1078`) is given the same
     tokenless POST. It passes with `_route: {noAuth: true}` or `route: {noAuth: true}`, and returns 403 without them or with `noAuth: false`.
   - **Source:** nothing in `packages/core/src` assigns `req._route` or `req.route`. `runMatchedRoute` sets only `req.params` (`server.ts:1180`).
   - **Live, with `TINA4_CSRF=true` and no token:** the no-auth POST gives 200 on py, php and rb, and 403 on nd.
   - **Live controls:** on every port, a session-authenticated tokenless write gives 403, so CSRF is really on.
     With `TINA4_CSRF=false`, both requests give 200.

Labels: every verdict above was established by running it. Only the "nothing assigns `_route`" part of claim 6 rests on a source grep.
The ch21 docs also read `$result['status']`, while the code returns `http_code`. That was read from the docblock at `Api.php:470-475` and was not run.
