# ruby and nodejs chapter 3 file-download calls do not match the API

The `response.file()` examples in ruby and nodejs chapter 3 (docs `docs/{ruby,nodejs}/03-request-response.md`,
book `book-3-ruby` / `book-4-nodejs` `chapters/03-request-response.md`) are copied from the python shape
`file(path, download_name)`. Neither port has that parameter.

Run on rb 50c5d2b / nd 44d433c (both 3.13.156), docs 2c09454, book 20b1006.

## What breaks, and why

- **ruby `file(path, "name.pdf")` → 500** `wrong number of arguments (given 2, expected 1)`. `response.rb:192`
  is `file(path, content_type: nil, download: false, root: nil)`; everything after `path` is a keyword.
- **nodejs `file(path, "name.pdf")` → 200 inline, no `Content-Disposition`.** `response.ts:379-382` takes
  `options?: {download, contentType, root}`; a string is read as that object and the name is dropped.
- **Neither port can set a download name.** With `download: true` / `{download: true}` the header is
  `attachment; filename="<basename>"` (rb `response.rb:244`, nd `response.ts` options.download branch). Only python
  has `download_name` (`response.py:390`); php's 3rd arg is the same bool (`Response.php:744`).
- **Prose:** both pages say plain `file(path)` adds `Content-Disposition`. Neither does without the download flag.
- **ruby §8 and §10 example paths 403.** `File.join(__dir__, "../../data/reports", f)` and `"../public/uploads"`
  keep a `..` segment, which `response.rb:209` refuses with 403 before any read (same defect php had in d-misc-02).
- **ruby §8 not-found branch 500s:** `return response.json(...)` inside the route block raises `unexpected return`
  (LocalJumpError; the handler is a proc called at `dispatch_pipeline.rb:805`). The framework's own skill and the
  page's §10 use `next`.

## Proof

`prove.sh` extracts every fenced block that calls `.file(` from each page, mounts it on a real server (route blocks
verbatim, ruby ones auto-discovered from `src/routes/`), and checks: 200 with the file's bytes; any two-argument call
gives `attachment`; route blocks answer 404 for a missing file; the page no longer makes the false prose claims.

```
DOCS=~/.cache/tina4-worktrees/drt08-tina4-documentation BOOK=~/.cache/tina4-worktrees/drt08-tina4-book ./prove.sh
```

`fix.py <docs> <book>` applies the fix; `SKIP=<1-4>` leaves one piece out. Logs: `stock.log` (docs/book ruby 2/11,
nodejs 6/11), `fixed.log` (all 11/11), `gates.log` (each piece left out fails only its own checks).

Setup (deps outside scratch): stock framework copies by `git archive` into
`~/.cache/tina4-worktrees/grind-1102/drt08/stock-tina4-{ruby,nodejs}`; nodejs node_modules hardlinked from
`verify-1029/d-cli-03/nodejs-run`, then `npm run build --workspace packages/core`.
