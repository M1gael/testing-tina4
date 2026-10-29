# ruby: `return` in a route block raises LocalJumpError, the route 500s

Ledger row `d-rt-06`. Rebuilt 2026-10-29 on: tina4-ruby 74aa1f5 (3.13.154, origin/v3),
tina4-documentation 01c4225, tina4-book 20b1006, ruby 3.4.10, prism 1.5.3.

## The defect

The ruby docs and book end route blocks early with `return response...`:

```ruby
Tina4::Router.get "/dashboard" do |request, response|
  if request.session["user_id"].nil?
    return response.redirect("/login")   # LocalJumpError: unexpected return -> 500
  end
  ...
end
```

`next response...` is the block's early exit.

## Mechanism (read, tina4-ruby 74aa1f5)

- `router.rb:512-518` `get`/`post` take `&block` and pass it to `add` (`:478`) as the handler;
  groups do the same at `:838` (`define_method(m) do |path, ..., &handler|`).
- `router.rb:760` route files are `load`ed; the block's home is that file's top level, which
  has finished by the time a request arrives.
- `dispatch_pipeline.rb:805` calls `ctx.route.handler.call(*args)` per request. The handler is a
  plain `Proc` (`lambda? == false`, run), so `return` tries to leave the finished top level:
  `LocalJumpError, "unexpected return"` (run). `rack_app.rb:188` turns it into a 500; the log
  says `500 Internal Server Error: unexpected return`.
- `return` inside a `def` or a lambda is fine and must be left alone.

## Classification (run, `classify.rb`: Prism over every ```ruby fence)

docs/ruby and book-3-ruby/chapters give identical results (same lines, same kinds):
57 route-block, 16 def, 4 lambda, 8 other-block (4 `Router.post(...).no_auth do` in ch10, row
d-rt-07; 4 `schema.add_query` resolvers in ch22). `textcount.rb` confirms Prism saw every textual
`return` (the one extra hit is inside a string in ch18). The 19 fences Prism reports errors on
contain no `return`.

The held patch changes 54 lines per tree, all `return` -> `next`, nothing else, all route-block
(run, `patchlines.rb` vs `classify.rb`). Left: 3 route-block returns in
`03-request-response.md`, sections 6 Cookies (:410), 8 File Downloads (:565), 10 Input
Validation (:651), in both trees. These are NOT d-rt-03's: its merged fix (docs #164, book #165)
changed the 9 upload-section returns in sections 7 and 12 only. `STRICT=1` counts and serves them.

Wider scope (run): every other ```ruby fence in both repos (course, general, other languages'
pages, public/skills, plan/, other books) has 0 route-block returns.

ch22 GraphQL: `return nil` inside `add_query` resolver blocks, called as a proc at
`graphql.rb:786`; inferred LocalJumpError, not run, not in this fix.

## Proof

```
W=~/.cache/tina4-worktrees/verify-1029/drt06
DOCS=$W/stock-docs BOOK=$W/stock-book ./prove.sh   # VERDICT FAIL ok=1 bad=10, rc 1
DOCS=$W/fixed-docs BOOK=$W/fixed-book ./prove.sh   # VERDICT PASS ok=11 bad=0, rc 0
STRICT=1 DOCS=$W/fixed-docs BOOK=$W/fixed-book ./prove.sh   # FAIL bad=4: the ch03 three
STOCK_DOCS=$W/stock-docs STOCK_BOOK=$W/stock-book FIXED_DOCS=$W/fixed-docs FIXED_BOOK=$W/fixed-book ./gate.sh
```

Served (real puma server, block copied verbatim from each tree into `src/routes/`):

| block | stock | fixed |
|---|---|---|
| ch02 POST /api/products `{}` | 500 unexpected return | 400 |
| ch08 POST /profile/update, no form token | 500 | 403 |
| ch10 GET /dashboard, no session | 500 | 302 |
| ch11 GET /api/products/1 twice (second is the cache hit) | 500 | 200 |
| control: `return` inside a `def`, called from a route | 200 | 200 |

POSTs carry a bearer token from `Tina4::Auth.get_token` (POST routes are secured by default).
`TINA4_SECRET` is a random value made per run; nothing is written to disk outside the throwaway
app dirs, which are deleted.

Gate (`gate.log`): each of the 12 files reverted alone, in each tree, turns prove.sh red; the
flagged counts sum to 54.

Note: the docs patch's 02-routing hunk header says line 851; the docs tip has it at 823. It
applies by offset, no fuzz. The book hunk is at 851 as written.

Logs: `stock.log`, `fixed.log`, `stock-strict.log`, `fixed-strict.log`, `gate.log`.
Trees, app dirs and HOME live in `~/.cache/tina4-worktrees/verify-1029/drt06/`, not here.
