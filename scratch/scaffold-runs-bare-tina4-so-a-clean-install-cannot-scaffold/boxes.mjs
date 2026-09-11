// One helper, used by repro.mjs and attack.mjs: build a throwaway machine and run ONE run_shell
// call on it. The machine is described by where the tina4 binary is, and by what is masked.
import { mkdtempSync, writeFileSync, chmodSync, mkdirSync, rmSync, copyFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import os from "node:os"; import path from "node:path";
import { fileURLToPath } from "node:url";

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const TSX = path.join(TREE, "node_modules/.bin/tsx");

// Stand-in for the CLI. We test whether the command is POINTED at it, not what it then does.
export function plant(at) {
  mkdirSync(path.dirname(at), { recursive: true });
  writeFileSync(at, "#!/bin/sh\necho FAKE_TINA4_RAN \"$@\"\nexit 0\n");
  chmodSync(at, 0o755);
}

// where        : path under $HOME to plant the CLI, or null for none
// maskUsrLocal : bind an empty dir over /usr/local/bin, so this host's real CLI cannot leak in
// bundled      : also plant beside a copy of node, and run with that node (execPath candidate)
// noNetwork    : run in a network namespace with no route, so a download cannot succeed
// homeSpace    : put a space in $HOME, to exercise the rewrite's quoting
export function box({ where, cmd, maskUsrLocal = false, bundled = false, noNetwork = false, homeSpace = false, withUv = false, extraPathDir = null }) {
  const home = mkdtempSync(path.join(os.tmpdir(), homeSpace ? "t4 home " : "t4-home-"));
  if (where) plant(path.join(home, where));
  // A stand-in `uv` in ~/.local/bin (a directory the PATH widening adds). uv lives in
  // /usr/local/bin or ~/.local/bin on a real box, and the first is masked in these cells -- so
  // without this, `uv run tina4 migrate` fails at `uv`, not at `tina4`, and the cell measures
  // nothing. It drops its own first argument ("run") and execs the rest, which is all the
  // rewrite cares about.
  if (withUv) {
    const uv = path.join(home, ".local/bin/uv");
    mkdirSync(path.dirname(uv), { recursive: true });
    writeFileSync(uv, "#!/bin/sh\nshift\nexec \"$@\"\n");
    chmodSync(uv, 0o755);
  }

  let runner = TSX, runnerArgs = ["child.mjs", cmd];
  if (bundled) {
    const dir = path.join(home, "bundle");
    mkdirSync(dir, { recursive: true });
    copyFileSync(process.execPath, path.join(dir, "node"));
    chmodSync(path.join(dir, "node"), 0o755);
    plant(path.join(dir, "tina4"));
    runner = path.join(dir, "node");
    runnerArgs = [path.join(TREE, "node_modules/tsx/dist/cli.mjs"), "child.mjs", cmd];
  }

  // extraPathDir: a directory that is on PATH but is NOT one of tina4Candidates()' fixed
  // locations -- the only way to exercise the PATH arm of findWorkingTina4().
  let PATH = "/usr/bin:/bin";
  if (extraPathDir) { plant(path.join(home, extraPathDir, "tina4")); PATH = `${path.join(home, extraPathDir)}:${PATH}`; }
  const env = { HOME: home, PATH, T4_TREE: TREE, T4_WIDEN: "1", TINA4_HOST: "127.0.0.1" };
  const inner = [runner, ...runnerArgs].map((x) => JSON.stringify(x)).join(" ");
  let argv;
  if (maskUsrLocal || noNetwork) {
    mkdirSync(path.join(home, "empty"), { recursive: true });
    const flags = "-r" + (noNetwork ? "n" : "") + (maskUsrLocal ? "m" : "");
    const pre = maskUsrLocal ? `mount --bind ${JSON.stringify(path.join(home, "empty"))} /usr/local/bin && ` : "";
    // --propagation is a mount-namespace option; passing it without -m is an error.
    const propagation = maskUsrLocal ? ["--propagation", "private"] : [];
    argv = ["unshare", [flags, ...propagation, "sh", "-c", `${pre}exec ${inner}`]];
  } else {
    argv = ["sh", ["-c", `exec ${inner}`]];
  }

  let raw = "";
  try {
    raw = execFileSync(argv[0], argv[1], { cwd: HERE, env, encoding: "utf8", timeout: 120_000, stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) { raw = String(e.stdout || "") + String(e.stderr || ""); }
  rmSync(home, { recursive: true, force: true });

  const line = raw.split("\n").find((l) => l.startsWith("__JSON__"));
  if (!line) return { noJson: true, raw: raw.slice(0, 500), home };
  return { ...JSON.parse(line.slice(8)), home };
}
