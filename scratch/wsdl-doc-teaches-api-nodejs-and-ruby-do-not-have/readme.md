# nodejs and ruby WSDL chapters teach an API neither port has

Ledger `d-api-01`. Rebuilt 2026-10-28 (the first version was lost to a cleanup and was never committed).

Pinned to: tina4-documentation origin/main 98c70a4, tina4-book origin/main 20b1006, tina4-nodejs origin/v3 b447252
(3.13.154, built with `npm run build`), tina4-ruby origin/v3 74aa1f5 (run from `lib/`). Stock frameworks live in
`~/.cache/tina4-worktrees/docfix-stock-{nodejs,ruby}`, detached at those commits. The fix is uncommitted on
branch `docs/dapi01-fix` in `~/.cache/tina4-worktrees/docfix-dapi01-{docs,book}`, cut from the tips above. It is
saved as `docfix-dapi01-docs.fix.patch` / `docfix-dapi01-book.fix.patch` beside them.

## Issue

**nodejs ch25** imports `WSDL`, `wsdl_operation` and `SOAPFault`, and calls `WSDL.load()`, `client.call()`,
`new WSDL({operations})`, `service.handler()` and `Router.all`. None of these exist. The package exports only
`WSDLService` and `@WSDLOperation` (`packages/core/src/index.ts:114`). A service is a subclass of `WSDLService`
(`wsdl.ts:293`) with methods decorated by `@WSDLOperation` (`:272`). It is served with `generateWSDL()` (`:396`)
and `handle(body)` (`:503`). There is no SOAP client. Decorating a plain function is a compile error under tsx:
"Decorators are not valid here".

**nodejs ch13** sections 9 and 11 start the app from `src/index.ts` with `new Tina4().start()`. There is no `Tina4`
export. The entry point is `app.ts` calling `startServer()` (`index.ts:25`).

**ruby ch25** uses `service_name`, `namespace`, `description`, `wsdl_operation :name, params:, returns: do`,
`wsdl_type` and `Router.mount_wsdl`, and it relies on `src/services` being autoloaded. The real DSL is
`wsdl_operation output: {...}` followed by a plain `def` (`lib/tina4/wsdl.rb:80`). Inputs are taken from the method
signature and always arrive as strings (`:97`). The service is named after the class (`:171`).
`Klass.new(request).handle` serves both GET `?wsdl` and POST (`:122`). Only `src/routes`, `src/api` and `src/orm`
are loaded (`lib/tina4.rb:996`). A raised error becomes the fault "Internal server error" unless TINA4_DEBUG is
set (`wsdl.rb:339`).

## Proof

`prove.sh [nd|rb]` takes every code block from the pages verbatim. Each block is written where its first-line path
comment says, or into `src/app` / `src/services` with a small loader when it has none. The script boots the real
server and runs the docs' own curl blocks, changing only the port. It then checks the values the page says you
will see. Choose pages with `DOCS=<docs tree>`, `BOOK=<book tree>` or `ND25=/ND13=/RB25=<file>`. The default is
tina4-documentation origin/main. Ports are 7341 (nd) and 7342 (rb). The script refuses to start on a busy port
and waits for the port to close after each stop. HOME is set to a temp dir.

The nodejs app is what `tina4 init` writes: `package.json` with `"type": "module"`. The ch13 entry block goes to the
file the section's prose names. That is `src/index.ts` on stock and `app.ts` on the fixed pages. N1 needs
dataaccess.com. N1 reports SKIP, not FAIL, when that service is unreachable or the fetch fails 3 times.

| | stock | fixed |
|---|---|---|
| docs 98c70a4 | 0/9 | 9/9 |
| book 20b1006 | 0/9 | 9/9 |

Stock docs, nd b447252 / rb 74aa1f5:

```
FAIL N1 25/2 client rc=1: SyntaxError: The requested module 'tina4-nodejs' does not provide an export named 'WSDL'
FAIL N2 25/3 decorator: .../block_3_1.ts:3:0: ERROR: Decorators are not valid here
FAIL N3 25/4-5 publish+call: app did not boot      (block_4_1.ts:4:0: ERROR: Decorators are not valid here)
FAIL N4 25/7 solution: app did not boot            (block_7_1.ts:10:0: ERROR: Decorators are not valid here)
FAIL N5 13/9 src/index.ts did not boot             (does not provide an export named 'Tina4')
FAIL N5 13/11 src/index.ts did not boot            (does not provide an export named 'Tina4')
FAIL R1 25/3-6: ... Failed to load src/routes/soap.rb: uninitialized constant CalculatorService
FAIL R2 25/8: ... NoMethodError: undefined method 'service_name' for class OrderService
FAIL R3 25/9: ... NoMethodError: undefined method 'wsdl_operation' for main
```

Fixed docs:

```
PASS N1 25/2 client: forty two
PASS N2 25/3 decorator publishes GetProductPrice
PASS N3 25/4-5 publish+call: <result>92</result>, doc shows <result>92</result>
PASS N4 25/7 solution: GetProduct + ListProducts(Electronics)=1,4
PASS N5 13/9 app.ts boots, 1 listener(s) registered
PASS N5 13/11 app.ts boots, 3 listener(s) registered
PASS R1 25/3-6 define+mount+call: <result>42</result>, doc shows <result>42</result>
PASS R2 25/8 fields+list: place_order total 9.5, list_skus 2 items
PASS R3 25/9 fault: production '<faultstring>Internal server error</faultstring>' as shown, debug shows the message
```

`gate.sh` starts from the fixed docs and puts back one stock piece at a time. It passes only if the single expected
check is the one that fails. There are 12 pieces, and all 12 are GATED:

- nd25 sections 2, 3, 4 and 7 turn N1, N2, N3 and N4 red.
- Dropping only `export const secure = false` turns N3 red (401 Unauthorized).
- nd13 sections 9 and 11 turn their own N5 red.
- rb25 sections 3 and 4, and dropping only `.no_auth` (401), turn R1 red.
- rb25 section 8 turns R2 red, and section 9 turns R3 red.

The site builds: `tina4press build .` (0.1.16) on a copy of the fixed docs tree reported 283 pages, exit 0.

## Cross-language

From the ledger row, not re-run here: py is clear (`WSDL` and `wsdl_operation` exist). php is clear (`Tina4\WSDL`,
`#[WSDLOperation]`).

## Not fixed here

nodejs ch27 `new Tina4()` uses the same blocks as the instance `ServiceRunner` API, which belongs to `d-svc-01`.
