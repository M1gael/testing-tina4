# Does tina4-python 3.13.139 refuse to boot without a 32-byte `TINA4_SECRET`?

Yes, by design (ADR-0079), and it is new in 3.13.139. Asked by a teammate upgrading an app.
Not a defect; no ledger row.

Run against tina4-python **3.13.139** and **3.13.138** from PyPI, Python 3.14.7, Linux.

## Mechanism

`server.py:4193` calls `require_boot_secret()` (`auth/__init__.py:243`) after
`ensure_dev_secret()`, and exits 1 on `InsecureSecretError`. The rule is
`MIN_SECRET_BYTES = 32` (`:215`), measured in UTF-8 bytes, so at least 32, not exactly 32:

- set but shorter than 32 bytes: refused in **every** mode, dev included;
- unset, not dev: refused;
- unset, dev (`TINA4_DEBUG=true`): a 64-char secret is minted into `.env.local` and it boots;
- RS256/RSA algorithms: not measured (PEM keys).

Added by `1d517410`. `require_boot_secret` is absent from 3.13.136 to 3.13.138.

## Proof

`./prove.sh` (or `PY=.venv138/bin/python ./prove.sh`). A "booted" result was spot-checked with
curl, which returned 200.

| cell | 3.13.138 | 3.13.139 |
|---|---|---|
| dev, unset | booted, minted | booted, minted |
| dev, 6 or 31 bytes | booted | refused, `Auth: TINA4_SECRET is N bytes` |
| dev or prod, 32 bytes | booted | booted |
| no debug, unset | booted, warning | refused |
| no debug, `token_hex(32)` | booted | booted |

A short secret set in `.env` (`changeme`) is refused as well, with rc 1.

## Notes

- The CHANGELOG 3.13.139 says "Production refuses to boot with a blank or short HMAC secret".
  It understates the change: a short secret is refused in dev too.
- `TINA4_DEBUG=true CI=true` with no secret boots but mints nothing. Signing then raises
  `InsecureSecretError`, so tokens fail rather than become forgeable. The blank-secret warning
  text says the run "was NOT detected as dev", which is wrong for that case. This is cosmetic.
- Changing the secret invalidates every JWT already issued (inferred).
- php, ruby and nodejs `origin/v3` carry a minimum-secret check (read, not run).
