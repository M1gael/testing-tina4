# Does a UTF-8 BOM hide the first `.env` variable from `tina4 serve`?

Yes — and from every other CLI reader of `.env`. Ledger row `f-cli-25`.

Run against: tina4 CLI **3.8.88** release (`~/.cache/tina4-update-probe/a/bin/tina4`, sha256
matches the release digest), source `origin/main` `ac9dca2`, Linux.

## Mechanism

Each reader does `read_to_string`, then `.lines()`, `trim()`, `split_once('=')`. `str::trim`
keeps U+FEFF (it is not Unicode whitespace), so the mark stays on the first key.

| Site | Entry point | Effect |
|---|---|---|
| `src/main.rs:620` | `tina4 serve` (no `-p`) | child gets `﻿FIRST_KEY`; `FIRST_KEY` unset |
| `src/main.rs:973` | `read_dotenv_bool_from` | BOM'd `TINA4_NO_BROWSER=true` ignored, browser opens |
| `src/env_config.rs:360` | `tina4 env --sync` | glued key written back mid-file, so the BOM is now inside the file |
| `src/env_migrate.rs:90` | `tina4 env --migrate` | legacy first key not renamed |

## Proof

```
./prove.sh                 # serve: exit 0 = defect present
./prove-other-readers.sh   # sync, migrate, no-browser: exit 0 = all broken
BIN=<fixed binary> ./prove.sh ...
```

Stock: `FIRST_KEY=<unset>`, `GLUED='﻿FIRST_KEY'`; readers: 3 broken, 0 ok.
Fixed (`fix.patch`, applied to `ac9dca2`): `FIRST_KEY=first`; readers: 0 broken, 3 ok.
`evidence/` holds the files `env --sync` and `env --migrate` wrote back on stock.

## Other ports (run, each port's own loader from `origin/v3`)

py, php and rb skip the first key with a warning (`invalid key '﻿FIRST_KEY', line
skipped`). nodejs reads it correctly.
