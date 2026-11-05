# What do the tina4-documentation CodeQL alerts need?

Question: for each of the 11 open CodeQL alerts on tina4-documentation (all on `origin/main`
92dde35921, fetched 2026-11-03), is it a real problem, and what change clears it?

Warrants: run = executed here; read = code read on 92dde35921, not run.

| # | where | verdict | fix that clears it |
|---|---|---|---|
| 12 | scripts/build-home.mjs:328 inline-script guard | **Real, low.** The build's own CSP guard misses `<SCRIPT>` and `</script >` (run, regex.log). The CSP still blocks them on tina4.com, so the page would break live instead of failing the build. | `/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi`; add `i` to the `<style` and `on…=` checks at :329-330 too. |
| 13, 14 | build-home.mjs:272, :283 | **Real, no security impact.** Only `.` is escaped before `new RegExp`; a name with another metachar (`a+b.js`) never matches (run). Names come from the repo's own home/ dir. | Full escape: `name.replace(/[.*+?^${}()\|[\]\\]/g, "\\$&")`. |
| 11 | build-home.mjs:302 | **Real, dead code.** `.replace(/^\n/, "\n")` swaps a newline for itself (run: output identical). | Delete the `.replace(...)`. |
| 16 | build-home.mjs:298-302 | **Not exploitable.** existsSync then read/write of the build's own dist/.htaccess in CI (read). | Drop existsSync; `try { readFileSync } catch (e) { if (e.code === "ENOENT") fail(...) }`. |
| 15 | scripts/preview-site.mjs:97-109 | **Not exploitable.** stat then readFile of local dist files, local preview server (read). | `const fh = await open(file); info = await fh.stat(); body = await fh.readFile()`, close in finally. |
| 7, 10 | .github/workflows/link-check.yml, audit-truth.yml | **Hardening.** No `permissions:`; token gets the repo default (could not read it: 403 for M1gael). Jobs only check out and run checks (read). | `permissions: { contents: read }` at top level. |
| 3 | .github/workflows/reindex-rag.yml | **Hardening.** Same; job uses only its own secrets, never the token (read). | `permissions: {}` (CodeQL's own suggestion). Keep `contents: read` if it checks out. |
| 6 | plan/v3/spikes/mqtt_spike3_auth_tls.py:62 | **False positive.** `ssl.create_default_context()` floors at TLS 1.2 since Python 3.10 (run: 3.14.8 minimum_version 771 = TLSv1_2). Spike file under plan/. | `ctx.minimum_version = ssl.TLSVersion.TLSv1_2`, or dismiss as "used in tests". |
| 5 | docs/public/gallery/08-datatable.html:168 | **False positive.** `Math.random()` makes fake salaries for a demo table. | Dismiss "false positive" (no code change). |

Net: 1 real defect (#12, the guard), 3 real code-quality bugs (#11, #13, #14), 2 races that are
not reachable (#15, #16), 3 workflow hardenings (#3, #7, #10), 2 false positives (#5, #6).

## Bounds

- The repo's default workflow token permission was not readable (403), so whether #3/#7/#10
  carry write access today is unknown.
- Nothing was built or deployed; fixes were not applied or tested.
- Not run: preview-site symlink handling. `normalize()` does not resolve symlinks, so a symlink
  inside dist pointing outside would be served (read, unpursued). The server also listens on all
  interfaces and proxies POST /v1/ask (read, unpursued).
