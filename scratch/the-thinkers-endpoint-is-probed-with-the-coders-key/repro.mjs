// Does the app send the CODER's API key to the THINKER's provider?
//
// app.ts:316 -- fetchModelContext() takes an `endpoint` argument but no token argument, and builds
// its header as `Bearer ${settings.token}` unconditionally. Both call sites (app.ts:528 and :1993 on
// main) pass settings.thinkerEndpoint for the thinker while the token stays the coder's.
//
// While both roles pointed at mcp.tina4.com with FREE-TOKEN this was invisible and harmless. It
// stops being either the moment the two endpoints are two different companies.
//
// Uses TINA4_* env overrides ONLY, so it runs on untouched source with no feature and no UI:
//   T4_TREE=/path/to/tree node repro.mjs
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const APP_PORT = Number(process.env.T4_PORT || 8786);
const A_PORT = Number(process.env.T4_A_PORT || 8921);   // coder's provider
const B_PORT = Number(process.env.T4_B_PORT || 8922);   // thinker's provider -- a different company
const KEY_A = "sk-CODER-aaaa";
const KEY_B = "sk-THINKER-bbbb";
const HOME = path.join(os.tmpdir(), "crosskey-" + process.pid);

const hits = { A: [], B: [] };
function provider(which, model) {
  return http.createServer((req, res) => {
    hits[which].push({ method: req.method, url: req.url, auth: req.headers.authorization || "" });
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ data: [{ id: model, context_window: 64000 }] }));
  });
}
const A = provider("A", "coder-model"), B = provider("B", "thinker-model");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

await new Promise((r) => A.listen(A_PORT, "127.0.0.1", r));
await new Promise((r) => B.listen(B_PORT, "127.0.0.1", r));
await fs.mkdir(path.join(HOME, "projects", "p"), { recursive: true });

const app = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
  cwd: TREE, detached: true, stdio: ["ignore", "ignore", "pipe"],
  env: { HOME, PATH: process.env.PATH, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(APP_PORT),
         TINA4_NO_BROWSER: "1", TINA4_PROJECTS_ROOT: path.join(HOME, "projects"),
         TINA4_CURRENT_PROJECT: "p", TINA4_STATE_DIR: path.join(HOME, ".tina4-simple-agent"),
         TINA4_MODEL_ENDPOINT: `http://127.0.0.1:${A_PORT}/v1`, TINA4_MODEL_ID: "coder-model", TINA4_MODEL_TOKEN: KEY_A,
         TINA4_THINKER_ENDPOINT: `http://127.0.0.1:${B_PORT}/v1`, TINA4_THINKER_MODEL: "thinker-model", TINA4_THINKER_TOKEN: KEY_B },
});
app.stderr.on("data", () => {});

let up = false;
for (let i = 0; i < 120 && !up; i++) { try { up = (await fetch(`http://127.0.0.1:${APP_PORT}/api/model`)).ok; } catch {} if (!up) await sleep(500); }
if (up) {
  // Startup already probes both. Poke it once more so the result does not depend on boot timing.
  await fetch(`http://127.0.0.1:${APP_PORT}/api/model`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
  await sleep(1500);
}
try { process.kill(-app.pid, "SIGTERM"); } catch {}
await sleep(400); A.close(); B.close();
await fs.rm(HOME, { recursive: true, force: true }).catch(() => {});

console.log(`  tree            ${TREE}`);
console.log(`  app came up     ${up}`);
for (const w of ["A", "B"]) {
  const auths = [...new Set(hits[w].map((h) => h.auth))];
  console.log(`  provider ${w} (${w === "A" ? "coder " : "thinker"})  ${hits[w].length} request(s)  auth: ${auths.join(" | ") || "none"}`);
}
const bGotCoderKey = hits.B.some((h) => h.auth === `Bearer ${KEY_A}`);
const bGotOwnKey = hits.B.some((h) => h.auth === `Bearer ${KEY_B}`);
console.log();
if (!up) { console.log("  UNPROVEN — the app never started, so nothing was measured"); process.exit(2); }
if (!hits.B.length) { console.log("  UNPROVEN — the thinker's provider was never contacted at all"); process.exit(2); }
console.log(bGotCoderKey
  ? `  REPRODUCED — the thinker's provider received the CODER's key (${KEY_A})`
  : `  not reproduced — the thinker's provider only ever saw ${bGotOwnKey ? "its own key" : "something else"}`);
process.exit(bGotCoderKey ? 0 : 1);
