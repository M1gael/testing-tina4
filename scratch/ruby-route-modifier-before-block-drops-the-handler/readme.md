# Ruby: a route block handed to a route modifier is dropped (d-rt-07)

The Ruby docs and book (ch10 Middleware & Security, ch36 Releases) register routes as

    Tina4::Router.post("/api/login").no_auth do |request, response| ... end

A `do` block binds to the last call in the chain, `no_auth`, not to `Router.post`. `Route#no_auth`,
`#secure`, `#cache` and `#middleware` take no block (tina4-ruby v3 85b72d7 `lib/tina4/router.rb:48-124`),
so Ruby drops it silently. `Router.post` got no block, so `add` registers the route with a `nil`
handler (`router.rb:537-538`). Every request to it then fails at
`dispatch_pipeline.rb:797` (`ctx.route.handler.parameters` -> "undefined method 'parameters' for nil")
and answers 500.

The API's own form (comments at `router.rb:47-124`): block on the verb, modifiers after `end`:

    Tina4::Router.post("/api/login") do |request, response| ... end.no_auth

## Files

- `classify.rb FILE.md...` — Prism-parses every ```ruby fence, lists route modifiers given a block
  (and no-argument modifiers given an argument, reported but not counted by prove.sh).
- `rewrite.rb FILE.md...` — the mechanical fix: moves the modifier chain after the block's `end`.
- `extract.rb FILE ANCHOR` — prints the fence holding ANCHOR, verbatim.
- `prove.sh` — static scan of docs/ruby and book-3-ruby/chapters, then serves ch10 samples verbatim
  on a real tina4-ruby server (HOME redirected, CSRF off) and requests them, with and without a token.
  `DOCS= BOOK= FW= ./prove.sh`
- `gate.sh` — reverts each changed file alone and confirms prove.sh goes red.

## Result (docs origin/main dfa88c2, book origin/main f74ab1e, tina4-ruby v3 85b72d7 / 3.13.158)

Stock (`stock.log`): 9 blocks on modifiers in docs, 9 in book; webhook and admin-users samples
answer 500 with or without a token. Fixed (`fixed.log`): 0 and 0; webhook 200 `{"received":true}`
with and without a token (`.no_auth` still applies), admin users 200 with a token and 401 without
(`.secure` still applies), the ch10 rate-limit sample 204 (placeholder handler runs), and a control
shows `end.no_auth.middleware(X)` runs X's hook. `gate.log`: each of the 4 files goes red alone.

## Not covered

- `.cache(ttl: 3600)` (ch36) and `.cache(300)` (docs index.md:479): `Route#cache` takes no argument,
  so these raise ArgumentError at load; and nothing reads the route's cached flag except the dev
  admin listing. Left as written: the right replacement is the maintainer's call. Separate ledger row (d-rt-09).
- ch10 login/logout/contact samples also `return` inside the route block (LocalJumpError, d-rt-06)
  and call an undefined `db`; not served here.
