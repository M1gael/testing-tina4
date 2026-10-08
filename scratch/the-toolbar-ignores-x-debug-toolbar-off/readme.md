# The toolbar ignores X-Debug-Toolbar: off

`docs/php/30-dev-tools.md` documents a way to keep the dev toolbar off one route: an
`X-Debug-Toolbar: off` response header. It does nothing; the toolbar is still injected.

Found while reading the docs for tina4-php#279. Ledger: `f-dev-04`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

`Tina4/Router.php:2594` `injectDevToolbar()` never reads the header, and no file in
`Tina4/` mentions it. py, rb and nd have no mention of it either (read).

## Run

```sh
TREE=<tina4-php tree> ./prove.sh
```

`app/` has three routes:

- `/on`: no header.
- `/off`: sets the header with `->header()`.
- `/doc-example`: the docs' own example.

## Result (`out-stock-3.13.148.txt`, PHP 8.4.26)

```
/on          toolbar markers: 1   X-Debug-Toolbar header sent: 0
/off         toolbar markers: 1   X-Debug-Toolbar header sent: 1
/doc-example toolbar markers: 0   X-Debug-Toolbar header sent: 0
```

`/off` sends the header and still gets the toolbar. The docs' own example answers
`$response->json(..., 200, ["X-Debug-Toolbar" => "off"])`: JSON never gets the
toolbar, and the header is not sent at all, so the example proves nothing either way.
No fix yet.
