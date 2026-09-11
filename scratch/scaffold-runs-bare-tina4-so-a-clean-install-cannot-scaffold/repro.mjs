// run-22 -- run_shell has no tina4 CLI resolution.
//
// phaseScaffold (app.ts:5060) issues the FIRST CLI call of every build as
//   runTool("run_shell", { cmd: `tina4 init python ${backendDir}` })
// and the run_shell dispatch (src/app/tools.ts:2417-2428) goes straight to runShell(). It never
// calls usesTina4Cli/ensureTina4/resolveTina4InCommand -- the three that spawn_service DOES call,
// twelve hundred lines earlier at tools.ts:2080, with a comment saying why: "a client may not
// have it on PATH -- resolve/download it and rewrite the command."
//
// Three boxes, one factor varied: WHERE the tina4 binary is.
//
//   A  downloaded    ~/.tina4-simple-agent/bin/tina4   where ensureTina4() puts it (tools.ts:692)
//   B  human install ~/.local/bin/tina4                a place app.ts:151 adds to PATH
//   C  this machine  /usr/local/bin/tina4              also added by app.ts:151
//
// A is the defect. B and C are the control: they prove the failure is not "run_shell is broken"
// but "run_shell depends on PATH, and two of the CLI's own homes are not on it".
//
// Box A is built inside a mount namespace with /usr/local/bin masked by an empty directory, so
// the real CLI on this host cannot leak in and make the run pass for the wrong reason.
//
// exit 0 = run_shell resolved the CLI on box A (fixed).  exit 1 = exit 127 (defect).
import { mkdtempSync, writeFileSync, chmodSync, mkdirSync, rmSync, copyFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import os from "node:os"; import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const TSX = path.join(TREE, "node_modules/.bin/tsx");
const SCAFFOLD = "tina4 init python .";   // the real phaseScaffold command
const CONTROL = "tina4 --version";        // same command-position `tina4`, no 60s venv build

// Stand-in for the CLI. We are testing whether the command is POINTED at it, not what it does.
function plant(at) {
  mkdirSync(path.dirname(at), { recursive: true });
  writeFileSync(at, "#!/bin/sh\necho FAKE_TINA4_RAN \"$@\"\nexit 0\n");
  chmodSync(at, 0o755);
}

function box(label, { where, cmd, maskUsrLocal, bundled }) {
  const home = mkdtempSync(path.join(os.tmpdir(), "t4-home-"));
  const planted = where ? path.join(home, where) : null;
  if (planted) plant(planted);

  // BUNDLED: the hand-delivered install DISTRIBUTION.md describes -- tina4 ships BESIDE the
  // executable, which is tina4Candidates()[0]: path.join(dirname(process.execPath), "tina4").
  // Reproduced by copying node into a directory that also holds the CLI and running the probe
  // with THAT node, so process.execPath points there.
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
  const env = { HOME: home, PATH: "/usr/bin:/bin", T4_TREE: TREE, T4_WIDEN: "1", TINA4_HOST: "127.0.0.1" };
  const inner = [runner, ...runnerArgs].map((x) => JSON.stringify(x)).join(" ");
  const argv = maskUsrLocal
    ? ["unshare", ["-rm", "--propagation", "private", "sh", "-c",
        `mount --bind ${JSON.stringify(path.join(home, "empty"))} /usr/local/bin && exec ${inner}`]]
    : ["sh", ["-c", `exec ${inner}`]];
  if (maskUsrLocal) mkdirSync(path.join(home, "empty"), { recursive: true });

  let raw = "";
  try {
    raw = execFileSync(argv[0], argv[1], { cwd: HERE, env, encoding: "utf8", timeout: 120_000, stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) { raw = String(e.stdout || "") + String(e.stderr || ""); }
  rmSync(home, { recursive: true, force: true });

  const line = raw.split("\n").find((l) => l.startsWith("__JSON__"));
  console.log(`\n--- ${label} ---`);
  if (!line) { console.log(`  NO JSON -- ${raw.slice(0, 500)}`); return null; }
  const j = JSON.parse(line.slice(8));
  console.log(`  tina4 binary at     ${bundled ? "$HOME/bundle/tina4 (beside the executable)" : planted ? "$HOME/" + where : "(none planted)"}`);
  console.log(`  /usr/local/bin      ${maskUsrLocal ? "MASKED (empty)" : "as on this host"}`);
  console.log(`  cmd                 ${cmd}`);
  console.log(`  usesTina4Cli(cmd)   ${j.usesTina4Cli}`);
  console.log(`  tina4Present()      ${j.tina4Present}`);
  console.log(`  would rewrite to    ${j.wouldRewriteTo}`);
  console.log(`  ok / exitCode       ${j.ok} / ${j.exitCode}`);
  console.log(`  cmd AS RUN          ${j.cmdAsRun || "(no result payload -- run_shell only returns one on success)"}`);
  console.log(`  stdout[0]           ${j.stdout}`);
  console.log(`  error               ${String(j.error).replace(/\n/g, " | ")}${j.capped ? "  (CAPPED)" : ""}`);
  return j;
}

console.log(`tree   ${TREE}`);
const A = box("BOX A -- CLI downloaded by ensureTina4(), /usr/local/bin masked",
  { where: ".tina4-simple-agent/bin/tina4", cmd: SCAFFOLD, maskUsrLocal: true });
const B = box("BOX B -- CLI installed by a human in ~/.local/bin, /usr/local/bin masked",
  { where: ".local/bin/tina4", cmd: SCAFFOLD, maskUsrLocal: true });
const C = box("BOX C -- this host, real tina4 on /usr/local/bin",
  { where: null, cmd: CONTROL, maskUsrLocal: false });
const D = box("BOX D -- hand-delivered bundle, tina4 beside the executable, /usr/local/bin masked",
  { where: null, cmd: SCAFFOLD, maskUsrLocal: true, bundled: true });

console.log("\n=== verdict ===");
if (!A) { console.log("FAIL: box A produced no result"); process.exit(2); }
const ranA = A.ok && /FAKE_TINA4_RAN/.test(String(A.stdout));
const ranD = !!D && D.ok && /FAKE_TINA4_RAN/.test(String(D.stdout));
if (ranA && ranD) {
  console.log("BOXES A and D: run_shell reached the CLI the agent itself owns. Scaffold survives. exit 0");
  process.exit(0);
}
console.log(`BOX A: ${String(A.error).split("\n").join(" | ")}`);
console.log(`  resolution was available the whole time -- tina4Present() found ${A.tina4Present}`);
console.log(`  and would have run: ${A.wouldRewriteTo}`);
console.log(`BOX B (human install): ok=${B?.ok} ranFake=${/FAKE_TINA4_RAN/.test(String(B?.stdout))}  <- PATH widening covers this one`);
console.log(`BOX C (this host):     ok=${C?.ok} stdout=${C?.stdout}  <- why the defect was never seen here`);
console.log(`BOX D (hand-delivered): ok=${D?.ok} ${String(D?.error).split("\n")[0]}`);
console.log("DEFECT REPRODUCED. exit 1");
process.exit(1);
