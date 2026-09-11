// Verbatim behaviour of app.ts:151-166 ("WIDEN PATH for a GUI-launched app"). Replicated rather
// than imported because importing app.ts boots the whole server. Kept identical on purpose: a
// reproduction that skips this proves a machine that cannot exist, since every real run of the
// agent has already widened PATH before phaseScaffold issues its first `tina4 init`.
//
// What it adds -- and what it does NOT. It adds the places a HUMAN installs a CLI: homebrew,
// /usr/local/bin, ~/.local/bin, ~/.bun/bin, ~/.cargo/bin, /usr/bin, /bin. It does not add either
// of the two places the AGENT ITSELF puts one: dirname(process.execPath) (the hand-delivered
// bundle -- DISTRIBUTION.md ships tina4 beside the executable) or ~/.tina4-simple-agent/bin
// (where ensureTina4()'s download lands, tools.ts:692). Those two are exactly the installs where
// a bare `tina4` cannot work.
import os from "node:os"; import path from "node:path"; import { existsSync } from "node:fs";

export function widenPath() {
  if (process.env.TINA4_NO_PATH_FIX === "1") return;
  const home = os.homedir();
  const candidates = process.platform === "win32" ? [] : [
    "/opt/homebrew/bin", "/opt/homebrew/sbin",
    "/usr/local/bin", "/usr/local/sbin",
    path.join(home, ".local", "bin"),
    path.join(home, ".bun", "bin"),
    path.join(home, ".cargo", "bin"),
    "/usr/bin", "/bin", "/usr/sbin", "/sbin",
  ];
  const cur = (process.env.PATH || "").split(path.delimiter).filter(Boolean);
  const seen = new Set(cur);
  const add = [];
  for (const d of candidates) { if (!seen.has(d) && existsSync(d)) { add.push(d); seen.add(d); } }
  if (add.length) process.env.PATH = [...add, ...cur].join(path.delimiter);
}
