# Does a CRUD list request put its own SQL in the query?

Ledger row **f-rt-03** (php v2 `Crud::getDataTablesFilter()` concatenated DataTables params
into SQL; fixed on v2 by PR #209). Open question: do the v3 ports carry the same class of defect?

**Answer: no. All four v3 ports are clear.** Every request-controlled value that reaches SQL in
the CRUD paths is bound, allow-listed against the model's declared fields, or integer-cast.
v3 has no DataTables-protocol endpoint at all (no `draw` / `columns[i][search]` handling).

Trees (stock upstream v3 tips, untouched):

| port | commit |
|---|---|
| tina4-python | `005f03a1` |
| tina4-php | `0a453208` |
| tina4-ruby | `0c8f3b5` |
| tina4-nodejs | `b2078dc` (v3.13.150) |

## Surface checked

Each port has two request-to-SQL paths: the **AutoCrud** REST routes (`GET/PUT/DELETE /api/{table}[/{id}]`)
and the **Crud.to_crud** server-rendered grid (model listing, and a developer-supplied custom `sql` listing).

| input | python | php | ruby | node |
|---|---|---|---|---|
| `search` (API) | bound `crud/__init__.py:132-133` | bound `AutoCrud.php:358-361` | bound `auto_crud.rb:401` | bound `orm/src/query.ts` `applySearch` |
| `search` (grid) | bound `crud/page.py:203-204,221-222` | bound `CrudData.php:82-84,118-121` | bound `crud.rb:375-376,402-404` | bound `orm/src/crud.ts:130-131,160-161` |
| `sort` (API) | declared field or ignored `crud/__init__.py:116-119` | resolved field or 400 `AutoCrud.php:599-623` | resolved field or 400 `auto_crud.rb:427-445` | resolved field or 400 `query.ts` `buildQuery`/`orderPart` |
| `sort` (grid) | declared field / SQL result column, else pk `crud/page.py:239-266` | same `CrudData.php:39-52` | same `crud.rb:351-357` | declared field else pk `crudHelpers.ts:83-91` |
| `sort_dir` | `== "desc"` → DESC else ASC (all ports, both paths) | | | |
| `filter[k]` | **not supported** (ignored) | key resolved or 400, value bound `AutoCrud.php:272-290,342-344` | same `auto_crud.rb:131-144` | same `query.ts` `buildQuery` |
| `limit/offset/page/per_page` | `int()` `crud/__init__.py:83-104` | `(int)` `AutoCrud.php:251-264`, `Crud.php:175` | `.to_i` `auto_crud.rb:101-113`, `crud.rb:68` | `parseInt` `query.ts:287-294`, `crud.ts:186` |
| `{id}` | `find_by_id` `WHERE pk = ?` | `load("pk = ?",[$id])` `AutoCrud.php:467-470` | `coerce_primary_key` + `find_by_id` `auto_crud.rb:380-383` | `[req.params.id]` bound `autoCrud.ts:276,390,414,423,446` |

Custom-`sql` grids interpolate the developer's own SQL and its own result-column names — not request data.

## Run evidence

Apps: `py/app.py`, `php/index.php`, `rb/app.rb`, `nd/app.ts` — each a real served app (sqlite,
`people` = Ann 30 / O'Brien 40 / Zed 25, plus a `secrets` table holding `TOPSECRET`), AutoCrud
registered public, `/grid` and `/gridsql` rendering `Crud.to_crud`. `prove.sh BASE_URL` fires the
probes; outputs in `*/prove.out`. Run with `HOME` redirected to a temp dir.

Key oracle: `sort=(CASE WHEN (SELECT token FROM secrets)='TOPSECRET' THEN -age ELSE id END)`.
Executed raw it orders **O'Brien,Ann,Zed** (checked directly with `sqlite3`); `sort=age` orders
Zed,Ann,O'Brien; the pk fallback orders Ann,O'Brien,Zed. So a raw sort is distinguishable.

| probe | python | php / ruby / node |
|---|---|---|
| control `search=O'Brien` | 1 row O'Brien (API + both grids) | same |
| `search=%' OR 1=1 --` | 0 rows | 0 rows |
| control `sort=age` | Zed,Ann,O'Brien | same |
| ORACLE sort, API | 200, Ann,O'Brien,Zed (ignored) | 400 UNKNOWN_FIELD |
| ORACLE sort, grid + gridsql | Ann,O'Brien,Zed (pk fallback) | same |
| `sort=name; --` | ignored | 400 |
| `sort_dir=desc, (select 1)` | ASC | ASC |
| `limit=1 union select 1,token,1 from secrets` | 3 rows (python `int()` fails → default 10) | 1 row (int-cast to 1), no TOPSECRET |
| `filter[name]=x' OR '1'='1` | ignored (no filter support) | 0 rows |
| `filter[name = name OR 1]=1` | ignored | 400 UNKNOWN_FIELD |
| `GET /api/people/9 OR 1=1` | 404 | 404 |
| `DELETE /api/people/9 OR 1=1` | 404, list still 3 rows | same |

No probe returned TOPSECRET, an SQL error, or extra rows anywhere.

## Side observations (not SQL injection; parity/behaviour only)

- **python AutoCrud list ignores `?filter[field]=value` entirely** — `filter[name]=O'Brien` returns
  all 3 rows (php/ruby/node return 1). No filter handling in `crud/__init__.py:198-210`.
- **python ignores an unknown `?sort`** (200, unsorted) where php/ruby/node 400 it, and does not
  support the `-field` descending form (`sort=-name` returned ascending).
- **node `?offset=` is rounded to a page boundary** (`query.ts:290-294`): `offset=1` with the
  default limit 100 returns from row 0.
- ruby and node wrap `GET /api/{table}/{id}` in `{"data": ...}`; python and php return the bare row.

## Not covered

- Only sqlite was run; the bound/allow-listed paths are engine-independent by reading.
- DocStore's `$regex`/REGEXP operators are a library API, not an HTTP CRUD endpoint — not audited here.
- A successful DELETE (control) was not run; the delete route shares the GET-by-id loader, whose control passed.

## How to run

`W=~/.cache/tina4-worktrees; export HOME=$(mktemp -d)` first (`W` before `HOME`), then from each sub-dir:

- py (7461): `PYTHONPATH=$W/tip-stock-py python3 app.py`
- php (7462): `TINA4_PHP_TREE=$W/tip-stock-php php $W/tip-stock-php/bin/tina4php serve 7462`
- rb (7463): `GEM_PATH=<real ~/.local/share/gem/ruby>:/usr/share/gems TINA4_RB_TREE=$W/tip-stock-rb ruby app.rb` (no bundler: the tree's lockfile wants gems not installed)
- nd (7464): `TINA4_DATABASE_URL=sqlite:///people.db TINA4_NO_BROWSER=true TINA4_ALLOW_PRIVATE_REQUESTS=true TINA4_SECRET=tina4-nodejs-test-suite-secret-0123456789abcdef $W/tip-stock-nd/node_modules/.bin/tsx --tsconfig $W/tip-stock-nd/tsconfig.json app.ts` (tsconfig `paths` keep it on `src/`, the orm `dist/` is not built per-file)

Then `../prove.sh http://localhost:PORT`. Free ports with `fuser -k PORT/tcp`.
