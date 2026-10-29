# nodejs docs call async ORM/DB APIs without await

Ledger `d-orm-01`. Run 2026-10-28 on host Linux, Node 22. Stock: tina4-nodejs origin/v3 b447252,
tina4-documentation origin/main 98c70a4, tina4-book origin/main 20b1006. Fix (uncommitted, branch
`docs/dorm01-fix` cut from those tips): `~/.cache/tina4-worktrees/docfix-dorm01-{docs,book}`, patches beside
them (`docfix-dorm01-{docs,book}.fix.patch`). `apply-fix.py <docs> <book>` makes the same edits on fresh trees
(checked: identical to the patched worktrees). Rebuilt here after the first proof (base docs 1828299, book
15ef833, nodejs 9559385) was deleted; every number below is from the rebuilt run.

**Issue.** Every Database/ORM call in tina4-nodejs returns a Promise, but the nodejs pages call many of them
bare: `const db = Database.getConnection();` then `db.fetch(...)` gives `TypeError: db.fetch is not a
function`; `post.belongsTo(...)` / `author.hasMany(...)` hand back a Promise, so `.toDict()` / `.map()` throw;
`Note.create()` / `qb.count()` / `qb.get()` serialise as `{}`. Read on b447252:

- `packages/orm/src/database.ts:1903` `export async function getConnection` (namespace `Database`)
- `packages/orm/src/baseModel.ts:546` `create`, `:715` `all`, `:755` `where`, `:514` `findById`, `:803` `save`,
  `:850` `delete`, `:1287` `hasOne`, `:1332` `hasMany`, `:1376` `belongsTo`, `:1273` `scope()` wraps `where`
- `packages/orm/src/queryBuilder.ts:280` `get`, `:320` `first`, `:337` `count`, `:375` `exists`

**Scope of the count** (`scan.py`): fenced ts/js/untagged blocks in `docs/nodejs/*.md`, `docs/general/*.md`
(tina4-documentation) and `book-4-nodejs/chapters/*.md`, `book-0-understanding/chapters/*.md` (tina4-book);
`36-releases.md` skipped (release history), `docs/public/skills/` out of scope. A call counts as un-awaited
unless the expression it heads is preceded by `await`/`yield`, is the whole value of a `return`, or is
followed by `.then(`. APIs: listed at the top of `scan.py`, plus model scopes the page itself declares.
The scan finds the same 178 hits on the base commits and on the tips (no new instances since base).

**Fixed** (145 of 178): add `await` (and `async` on the enclosing function where it had none):
ch05, 08, 11, 15, 30, 31, 34, 35, index (`getConnection`), ch06 (`create`, `hasMany`, `belongsTo`, `hasOne`,
scopes), ch07 (`qb.count`/`get`), ch18 §11 plain functions, ch26 (container `get`/singleton), ch29 (test
function, `create_note` tool), general 03 (both), general frond.md `pushLive`. Book mirrors docs line for line.

**Left alone** (33, `excluded.txt`): `await` cannot fix them, the framework does not await the callback (read):
- ch18 §5 and §11 `tests()` blocks: `runAll()` (`core/src/testing.ts:108`) calls `fn(...args)` without await
  (`:174`, `:187`, `:200`, `:208`), so an async test returns a Promise and `expectTrue` passes vacuously.
- ch29 `mcpResource` handlers: `resource.handler()` not awaited (`core/src/mcp.ts:654`; tools are, `:615`).
- general frond.md `Frond.liveSource`: `LiveProvider` typed sync (`frond/src/engine.ts:30`), called bare (`:3657`).

**prove.sh** counts un-awaited calls, then serves five doc blocks verbatim on the real server (app copied to
a mktemp dir, `node_modules/tina4-nodejs` symlinked to `NODEJS`, port 7463), for docs and book trees:
ch05 "Getting the Database Object", ch06 hasMany route, ch06 belongsTo route, ch06 `Note.create`,
ch07 "List Endpoint with Filters". `NODEJS` defaults to `~/.cache/tina4-worktrees/dorm01-stock-nodejs`
(b447252, `npm run build --workspaces`). `VERBOSE=1` lists the hits and server errors.

    ./prove.sh          # stock: 178 found, 33 excluded, 145 to fix; 10 of 10 samples fail; exit 1
    DOCS=~/.cache/tina4-worktrees/docfix-dorm01-docs BOOK=~/.cache/tina4-worktrees/docfix-dorm01-book ./prove.sh
                        # fixed: 33 found, 33 excluded, 0 to fix; 0 of 10 fail; exit 0

Stock sample failures: `db.fetch is not a function`, `posts.map is not a function`, `author.toDict is not a
function` (500s), `{"isNote":false,"id":null}`, `{"products":{},"total":{}}`.

Reverting each piece alone on the fixed trees goes red: getConnection files 90 to fix (+2 samples), ch06 26
(+6), ch07 6 (+2), ch18 12, ch29 4, choosing 4, ch26 2, frond 1 (sum 145). The ch18/ch26/ch29/choosing/frond
pieces gate on the count only; no sample executes them. `tina4press build .` on the fixed docs tree:
283 pages, exit 0.

**Other ports.** Python, PHP and Ruby Database/ORM APIs are synchronous (`def get_connection`, etc.): n/a.

**Found on the way** (not fixed here, read on b447252):
- `Database.getConnection()` opens a new connection and replaces the global adapter on every call
  (`database.ts:1903` -> `initDatabase` `:1928`), yet ch05 says it "returns the active database connection"
  and the examples call it per request.
- `createTable()` run before any instance exists makes camelCase columns (`authorId`) while `save()` writes
  snake_case (`author_id`): autoMap fills `fieldMapping` in the constructor (`baseModel.ts:264-270`). The
  app here creates `authors`/`posts` by SQL to step round it.
- ch29 `testMcpToolCall` does `JSON.parse(mcp.handleMessage(...))`; `handleMessage` is async.
- general 03 `Product.select({ page })`: `select` takes SQL, not an options object.
