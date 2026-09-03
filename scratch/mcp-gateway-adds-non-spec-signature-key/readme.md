# The tina4-coder MCP gateway puts a non-spec `signature` key on the JSON-RPC envelope

`https://mcp.tina4.com/mcp` cannot be used from Claude Code, or from any other MCP client that
validates messages against the specification. The HTTP layer is fine — `initialize` returns
200 with a complete tools list — but the client discards every message the server sends.

**Run against:** gateway `serverInfo` `tina4-coder` 1.0.0, protocol `2025-06-18`, observed
2026-09-03. Client: Claude Code 2.1.259. Schema checks: `@modelcontextprotocol/sdk` 1.30.0.

Nothing here is a defect in tina4-python / -php / -ruby / -nodejs / -js. See *Blast radius*.

## 1. Reproduce

`./prove.sh` — read-only, uses the public demo bearer `FREE-TOKEN` documented at
`tina4-simple-agent/README.md:162`. Exits 1 while the defect is present.

```
  http=200  initialize             top-level keys: jsonrpc id result signature        <- NON-SPEC
  http=200  tools/list             top-level keys: jsonrpc id result signature        <- NON-SPEC
  http=200  error -32601           top-level keys: jsonrpc id error signature         <- NON-SPEC
  http=200  error -32603           top-level keys: jsonrpc id error signature         <- NON-SPEC
  http=200  error -32700           top-level keys: jsonrpc id error signature         <- NON-SPEC
  http=401  no Authorization       top-level keys: jsonrpc id error                   ok
```

The envelope as shipped:

```json
{"jsonrpc":"2.0","id":1,"result":{...},"signature":"🎋 Tina4 Thinker"}
```

End to end, with the server registered in Claude Code at local scope:

```
tina4-coder: https://mcp.tina4.com/mcp (HTTP) - ✘ Failed to connect — [ { "code": "invalid_union", ...
  { "code": "unrecognized_keys", "keys": [ "result", "signature" ], "path": [],
    "message": "Unrecognized keys: \"result\", \"signature\"" } ...
```

## 2. Mechanism

> A top-level key that is not `jsonrpc` / `id` / `method` / `params` / `result` / `error` makes
> the envelope match none of the four members of the client's message union, so the message is
> rejected before its contents are ever looked at.

`@modelcontextprotocol/sdk/dist/esm/types.js`:

| line | what |
|---|---|
| `types.js:114` | `JSONRPCRequestSchema` — `z.object({...}).strict()` |
| `types.js:125` | `JSONRPCNotificationSchema` — `.strict()` |
| `types.js:135` | `JSONRPCResultResponseSchema` — `{jsonrpc, id, result}`, `.strict()` |
| `types.js:175` | `JSONRPCErrorResponseSchema` — `{jsonrpc, id, error}`, `.strict()` |
| `types.js:210` | `JSONRPCMessageSchema` — `z.union([...those four])` |
| `types.js:100` | `ResultSchema` — `z.looseObject({...})`, so extra keys **inside** `result` are kept |

`.strict()` on all four members is what does it. The union reports every member's failure, which
is why the error names a missing `method` (the Request and Notification members) alongside
`unrecognized_keys` (the Response and Error members) — exactly the shape Claude Code prints.

The reporter's description of the mechanism was correct. Two details it got wrong are in
*Corrections*.

## 3. Causation, both directions

`proxy.py` sits in front of the live gateway and varies exactly one factor — where the
`signature` key sits. Everything else on the wire is upstream's own bytes. Verdicts are from
`claude mcp list` against Claude Code 2.1.259.

| `MODE` | envelope | Claude Code |
|---|---|---|
| `passthrough` | as upstream ships it | **FAILED** (control) |
| `drop` | `signature` removed | **CONNECTED** |
| `into-result` | moved to `result.signature` | **CONNECTED** |

`passthrough` is the control: it proves the proxy is not what makes the other two connect.
`drop` is necessary — remove only that key and the client attaches. `into-result` is
sufficient — the key is still there, carrying the same value, and the client attaches, so it is
the *placement* that breaks it and not the presence of the data.

`validate-variants.mjs` checks the same variants directly against SDK 1.30.0 schemas, plus the
result-level schemas the client applies afterwards:

```
FAIL as-shipped   initialize / tools/list / error
PASS FIX-A drop            initialize / tools/list / error
PASS FIX-B result.sig      initialize / tools/list
FAIL FIX-B result.sig      ON ERROR (an error envelope has no result to put it in)
PASS FIX-C result._meta.signature
PASS FIX-D error.data.signature
PASS FIX-E error.signature       (silently stripped — parsed object keeps only code, message)
InitializeResultSchema w/ result.signature : true
ListToolsResultSchema  w/ result.signature : true
```

## 4. Corrections to the report as drafted

Both matter to whoever writes the patch.

- **"at the top level of every JSON-RPC envelope" — not every one.** The 401 from the
  unauthenticated path is clean (`jsonrpc`, `id`, `error`). The key is added by the JSON-RPC
  dispatch layer, which sits behind the auth gate. A patch that only fixes the success path
  will leave the four error classes broken.
- **"move it inside `result`" does not cover errors.** The gateway stamps `signature` on error
  envelopes too (`-32601`, `-32603`, `-32700` all confirmed above), and an error envelope has
  no `result`. Adding one produces `{jsonrpc, id, error, result}`, which fails `.strict()` just
  the same — verified, `FIX-B ... ON ERROR` above.

So the honest options are: **drop it** (one change, covers every path), or **`result.signature`
for successes and `error.data.signature` for errors** (two changes, both verified to parse).
Dropping it is the one to recommend.

## 5. Blast radius

The gateway is not any of the shipped ports. Every port builds the envelope with three keys and
nothing else, and none contains the string anywhere:

| port | envelope built at | signature key |
|---|---|---|
| tina4-python | `tina4_python/mcp/protocol.py:19,31,39` | none |
| tina4-php | `Tina4/Bootstrap/MCP.php:88,104,115` | none |
| tina4-ruby | `lib/tina4/mcp.rb:40,51,59` | none |
| tina4-nodejs | `packages/core/src/mcp.ts:110,123,127` | none |
| tina4-js | no MCP server | n/a |

`grep -rn "Thinker"` across every checkout in `gitdir/tinaforks/` returns nothing. The string
exists in no repository we hold, so **the fix cannot be written here** — it belongs to whoever
deploys `tina4-coder`. That is the reason this project has no candidate patch and no fork
branch; there is no source tree to put one in.

The `-32700` text is `Invalid JSON: Expecting ',' delimiter: line 1 column 24 (char 23)` — a
verbatim CPython `json` decoder message, so the gateway is Python. It is not tina4-python's MCP
module, whose tools are `api_*` / `code_search` / `docs_*`; the gateway serves `tina4_code`
and friends.

## 6. Residual gaps

- **Not tested against a real SSE stream.** Every response observed was
  `content-type: application/json`; the server never opened `text/event-stream`, so whether it
  stamps `signature` on streamed notifications is unknown. If it does, the same break applies
  and `prove.sh` will not catch it.
- **`notifications/initialized` returns 202 with an empty body** — correct, and it carries no
  envelope to stamp.
- **Only the `FREE-TOKEN` tier was exercised.** A profile token may reach a different code path.
- **`drop` and `into-result` were confirmed to make Claude Code attach**, not to make every
  subsequent tool call work. Connection is as far as this went.
- Whether the key is deliberate branding or debug residue is not established — that is a
  question for the gateway's author, and it decides between "drop" and "relocate".

## Files

| | |
|---|---|
| `prove.sh` | the reproduction; exits 1 while the defect is present |
| `proxy.py` | single-factor proxy, `MODE=passthrough\|drop\|into-result` |
| `validate-variants.mjs` | candidate placements against SDK 1.30.0 schemas |
| `evidence/*.raw`, `*.hdr` | the captured envelopes and response headers |

---

## Closed — fixed upstream 2026-09-03

The gateway was patched the same day. Re-checked 13:49 UTC:

```
  http=200  initialize             top-level keys: jsonrpc id result        ok
  http=200  tools/list             top-level keys: jsonrpc id result        ok
  http=200  error -32601           top-level keys: jsonrpc id error         ok
  http=200  error -32603           top-level keys: jsonrpc id error         ok
  http=200  error -32700           top-level keys: jsonrpc id error         ok
  http=401  no Authorization       top-level keys: jsonrpc id error         ok

PASS - every envelope is jsonrpc/id/result|error only
```

They kept the branding and relocated it, rather than dropping it — `result._meta.signature`,
which is `FIX-C` in section 3:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18",
 "capabilities":{...},"serverInfo":{"name":"tina4-coder","version":"1.0.0"},
 "_meta":{"signature":"🎋 Tina4 Thinker"}}}
```

`_meta` is the specification's own extension slot and `ResultSchema` (`types.js:100`) is a
`z.looseObject`, so it validates. All four error classes are clean too, which was the half of
the fix the original report would have missed.

End to end, Claude Code 2.1.259:

```
tina4-coder: https://mcp.tina4.com/mcp (HTTP) - ✔ Connected
```

Post-fix envelope kept at `evidence/init-after-fix.raw`. `prove.sh` now exits 0 and stays
useful as a regression check — if the key ever comes back to the top level it goes red again.

**Never filed anywhere.** No ledger row, no GitHub issue: the gateway is a hosted service with
no repository in `gitdir/tinaforks/`, and it was reported and fixed in Slack the same day.
Nothing to close but this file.
