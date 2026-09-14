// sec-03: does TINA4_STATE_DIR isolate GLOBAL SECRETS, as app.ts:427 says it isolates
// "the whole state dir"?
//
// Boot the app with BOTH a redirected state dir and a FAKE HOME, then save a global secret
// through the public route. Under the documented behaviour the file lands in the state dir.
//
// The fake HOME is not decoration: the only isolation that currently works is overriding HOME,
// so it is what keeps this probe from writing into Michael's real
// ~/.tina4-simple-agent/secrets/ -- which is exactly how this defect was found on 2026-09-09.
// The probe asserts afterwards that the real home was NOT touched.
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE   = process.argv[2] || process.cwd();
const PORT   = Number(process.env.PORT || 8931);
const BOX    = await fs.mkdtemp(path.join(os.tmpdir(), "sec03-"));
const HOME   = path.join(BOX, "home");        // fake home, so the real one is never a target
const STATE  = path.join(BOX, "state");       // what TINA4_STATE_DIR points at
const REAL   = path.join(os.homedir(), ".tina4-simple-agent", "secrets");
const NAME   = "SEC03_PROBE_" + process.pid;
const CAP_MS = 60_000;

const realBefore = await fs.readdir(REAL).catch(() => null);

await fs.mkdir(HOME, { recursive: true });
await fs.mkdir(STATE, { recursive: true });

// A stale server on this port makes every check below read the OLD code as a fresh success --
// the exact trap CLAUDE.md names. Refuse to start rather than report a result from someone else's
// process.
if (await fetch(`http://127.0.0.1:${PORT}/api/model`).then(() => true).catch(() => false)) {
  console.log(`VERDICT: CANNOT RUN -- something is already listening on ${PORT}. Kill it first.`);
  process.exit(2);
}

const app = spawn("setsid", ["npx", "tsx", "app.ts"], {
  cwd: TREE,
  env: { ...process.env,
    HOME, USERPROFILE: HOME,
    TINA4_STATE_DIR: STATE,
    TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(PORT),
    TINA4_PROJECTS_ROOT: path.join(BOX, "projects"),
    TINA4_NO_BROWSER: "1", TINA4_DEBUG: "false" },
  stdio: ["ignore", "ignore", "pipe"], detached: true,
});
let stderr = ""; app.stderr.on("data", (d) => (stderr += String(d)));

const deadline = Date.now() + CAP_MS;
let up = false;
while (Date.now() < deadline && !up) {
  up = await fetch(`http://127.0.0.1:${PORT}/api/model`).then((r) => r.ok).catch(() => false);
  if (!up) await new Promise((r) => setTimeout(r, 400));
}

const out = { up, saved: null, inState: null, inFakeHome: null, realUntouched: null, err: null };
try {
  if (!up) throw new Error(`app did not answer on ${PORT} within ${CAP_MS}ms. stderr: ${stderr.slice(-400)}`);
  const r = await fetch(`http://127.0.0.1:${PORT}/api/global-secrets`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: NAME, value: "probe-value-never-a-real-key" }),
  });
  out.saved = await r.json();
  out.inState     = await fs.readFile(path.join(STATE, "secrets", NAME), "utf8").then(() => true).catch(() => false);
  out.inFakeHome  = await fs.readFile(path.join(HOME, ".tina4-simple-agent", "secrets", NAME), "utf8").then(() => true).catch(() => false);
} catch (e) { out.err = String(e.message || e); }

// kill the whole process group -- npx tsx leaves a child otherwise -- then READ THE PORT BACK,
// because a leaked server is what makes the next run believe someone else's process is its own.
try { process.kill(-app.pid, "SIGKILL"); } catch {}
try { process.kill(app.pid, "SIGKILL"); } catch {}
const portFree = async () => !(await fetch(`http://127.0.0.1:${PORT}/api/model`).then(() => true).catch(() => false));
let freed = false;
for (let i = 0; i < 15 && !freed; i++) { freed = await portFree(); if (!freed) await new Promise((r) => setTimeout(r, 200)); }
if (!freed) {
  // `npx -> tsx -> node` puts the real server two levels down and it does not always land in the
  // group we signalled, so go by the PORT: whoever holds it is the thing to kill.
  const { execSync } = await import("node:child_process");
  try {
    const out = execSync(`ss -ltnp 2>/dev/null | grep ':${PORT} ' || true`, { encoding: "utf8" });
    for (const m of out.matchAll(/pid=(\d+)/g)) { try { process.kill(Number(m[1]), "SIGKILL"); } catch {} }
  } catch {}
  for (let i = 0; i < 15 && !freed; i++) { freed = await portFree(); if (!freed) await new Promise((r) => setTimeout(r, 200)); }
}
if (!freed) console.log(`WARNING: port ${PORT} still answering after the kill -- a server leaked.`);

const realAfter = await fs.readdir(REAL).catch(() => null);
out.realUntouched = JSON.stringify(realBefore) === JSON.stringify(realAfter);

console.log(JSON.stringify(out, null, 1));
await fs.rm(BOX, { recursive: true, force: true });
if (out.err) { console.log(`\nVERDICT: CANNOT RUN -- ${out.err}`); process.exit(2); }
if (!out.realUntouched) { console.log("\nVERDICT: CANNOT TRUST -- the REAL secrets dir changed during this run."); process.exit(2); }

const isolated = out.inState === true && out.inFakeHome === false;
console.log(isolated
  ? "\nVERDICT: ISOLATED -- the secret landed under TINA4_STATE_DIR. sec-03 does not reproduce."
  : "\nVERDICT: NOT ISOLATED -- sec-03 reproduces. TINA4_STATE_DIR was ignored; the secret went to "
    + (out.inFakeHome ? "$HOME/.tina4-simple-agent/secrets (the real home, but for the HOME override)" : "neither location"));
process.exit(isolated ? 0 : 1);
