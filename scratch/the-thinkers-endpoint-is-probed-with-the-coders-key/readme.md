# The thinker's endpoint is probed with the coder's API key

**Found** 2026-09-11, while attacking the w-20 build (API-key providers in Settings).
**Present on untouched `main`** — `v0.2.0-295-g9d159fe` / `baseline-main` at `d719fc3`. Not
introduced by w-20; w-20 is what turns it from invisible into a credential leak.

## What happens

`fetchModelContext()` takes an `endpoint` argument and no token argument. It builds its header
from `settings.token` — the **coder's** token — whatever endpoint it was handed:

```
app.ts:316   const r = await fetch(`${base}/models`, { headers: { authorization: `Bearer ${settings.token}` } });
```

Both callers pass the thinker's endpoint with no way to pass the thinker's token:

```
app.ts:528   return Promise.all([fetchModelContext(), fetchModelContext(settings.thinkerEndpoint, settings.thinkerModel)]);
app.ts:1993  await Promise.all([fetchModelContext().catch(...), fetchModelContext(settings.thinkerEndpoint, settings.thinkerModel).catch(...)]);
```

(line numbers on `main` `d719fc3`; the same three lines are 317 / 544 / 2026 on the w-20 build)

So every startup and every settings save sends the coder's bearer token to the thinker's
provider. While both roles pointed at `https://mcp.tina4.com/v1` with `FREE-TOKEN` this was
invisible and cost nothing. It stops being either as soon as the two endpoints are two different
companies — which is exactly what w-20 is for.

## Reproduction

Two recording servers stand in for two providers. The app is pointed at one for each role with a
**different key each**, using `TINA4_*` env overrides only — so it runs on untouched source, with
no feature and no UI involved.

```sh
T4_TREE=/var/home/work/gitdir/tina4-simple-agent-work/baseline-main node repro.mjs
```

Untouched `main`:

```
  provider A (coder )  2 request(s)  auth: Bearer sk-CODER-aaaa
  provider B (thinker)  2 request(s)  auth: Bearer sk-CODER-aaaa

  REPRODUCED — the thinker's provider received the CODER's key (sk-CODER-aaaa)
```

The thinker's provider is **never** contacted with its own key. Both of its requests carry the
coder's.

## Impact

A user who follows w-20's own headline case — OpenRouter for the coder, DeepSeek for the thinker —
hands their OpenRouter key to DeepSeek, and vice versa on the other side of a swap. Neither
provider asked for it and neither is doing anything wrong; the key simply arrives. The endpoint is
user-typed, so it can be *any* host, including one chosen by whoever suggested a settings snippet.

Not a turn path — this is the `/models` capability probe, which runs on boot and on every
`POST /api/model`. The chat paths (`coderStream` / thinker stream) do carry the right token per
role; this is the one site that does not.

## Fix, as built on `scratch` (uncommitted)

Give the token the same treatment as the endpoint — pass it in, default it to the coder's:

```
async function fetchModelContext(endpoint = settings.endpoint, model = settings.model, token = settings.token)
  ... authorization: `Bearer ${token}`
```

and both thinker call sites pass `settings.thinkerToken`. Same file, three lines.

After the fix, on the same reproduction:

```
  provider B (thinker)  2 request(s)  auth: Bearer sk-THINKER-bbbb
  not reproduced — the thinker's provider only ever saw its own key
```

## Files here

| | |
|---|---|
| `repro.mjs` | the reproduction. Exit 0 = leak present, 1 = absent, 2 = nothing measured |
| `readme.md` | this |
