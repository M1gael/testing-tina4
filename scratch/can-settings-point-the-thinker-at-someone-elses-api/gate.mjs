// w-20 GATE -- written BEFORE the code, and it must fail on the untouched tree.
//
// The sentence it checks:
//
//   "A third-party OpenAI-compatible provider with an API key can be selected for EITHER role from
//    Settings: the selection STICKS (a following GET reports that endpoint, not the gateway),
//    SURVIVES a restart, the key is never returned by any GET and never lands world-readable, and a
//    REAL TURN's request arrives at that provider carrying `Authorization: Bearer <key>` and the
//    chosen model id."
//
// Deliberately NOT via TINA4_* env overrides. Those already work today and bypass everything this
// feature is about -- reconcileVendorWiring() skips a field whose env var is set, so a gate using
// them would be green on the untouched tree and prove nothing.
//
//   T4_TREE=<tree> node gate.mjs        exit 0 = feature present, exit 1 = absent
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import { existsSync, statSync, readFileSync } from "node:fs";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const APP_PORT = Number(process.env.T4_PORT || 8799);
const FAKE_PORT = Number(process.env.T4_FAKE_PORT || 8901);
const KEY = "sk-or-v1-GATEKEY-9f3c";           // must never appear in a GET or in a 0644 file
const MODEL = "deepseek/deepseek-chat";         // must appear on the wire
const HOME = path.join(os.tmpdir(), "w20-gate-" + process.pid);
const STATE = path.join(HOME, ".tina4-simple-agent");
const PROJECTS = path.join(HOME, "projects");

// ---- the third party. Records what it was actually called with.
const seen = [];
const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
const fake = http.createServer((req, res) => {
  if (req.method === "GET") {            // /models probe, used by fetchModelContext and by verify
    seen.push({ kind: "models", auth: req.headers.authorization || "", url: req.url });
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ data: [{ id: MODEL, context_window: 64000 }] }));
    return;
  }
  let body = ""; req.on("data", (c) => (body += c));
  req.on("end", () => {
    let b = null; try { b = JSON.parse(body); } catch {}
    seen.push({ kind: "chat", auth: req.headers.authorization || "", model: b?.model, url: req.url, stream: b?.stream !== false });
    const maxTok = Number(b?.max_tokens ?? 0);
    const sys = String(b?.messages?.[0]?.content ?? "");
    // Same shape as test/turn-harness.mjs: answer plausibly or the app reads it as an offline stub,
    // fires open-setup and abandons the turn -- which looks like a pass with zero requests.
    const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
      : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
      : "It is a small static page. Nothing is broken.";
    if (b && b.stream === false) {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }],
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } }));
      return;
    }
    res.writeHead(200, { "content-type": "text/event-stream" });
    sse(res, { choices: [{ delta: { role: "assistant" } }] });
    sse(res, { choices: [{ delta: { content: answer } }] });
    sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
    sse(res, { choices: [], usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } });
    res.write("data: [DONE]\n\n"); res.end();
  });
});

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ENDPOINT = `http://127.0.0.1:${FAKE_PORT}/v1`;
let app = null;
function boot() {
  app = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
    cwd: TREE, detached: true, stdio: ["ignore", "ignore", "pipe"],
    // NO TINA4_MODEL_* / TINA4_THINKER_* here, on purpose (see the header).
    env: { HOME, PATH: process.env.PATH, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(APP_PORT),
           TINA4_NO_BROWSER: "1", TINA4_PROJECTS_ROOT: PROJECTS, TINA4_CURRENT_PROJECT: "p",
           TINA4_STATE_DIR: STATE, TINA4_THINKER_PLAN: "0" },
  });
  app.stderr.on("data", () => {});
}
const stop = () => { try { process.kill(-app.pid, "SIGTERM"); } catch {} };
async function upHttp(tries = 120) {
  for (let i = 0; i < tries; i++) { try { const r = await fetch(`http://127.0.0.1:${APP_PORT}/api/model`); if (r.ok) return true; } catch {} await sleep(500); }
  return false;
}
const get = () => fetch(`http://127.0.0.1:${APP_PORT}/api/model`);
const post = (b) => fetch(`http://127.0.0.1:${APP_PORT}/api/model`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(b) });

class Session {
  constructor(sid) { this.sid = sid; this.ws = null; this.waiter = null; }
  open() { return new Promise((resolve) => {
    this.ws = new WebSocket(`ws://127.0.0.1:${APP_PORT}/ws/agent`);
    this.ws.onopen = () => { this.ws.send(JSON.stringify({ type: "session:activate", id: this.sid, project: "p" })); setTimeout(resolve, 600); };
    this.ws.onmessage = (ev) => { let m; try { m = JSON.parse(ev.data); } catch { return; }
      if (!this.waiter) return; this.waiter.frames.push(m);
      if (m.type === "turn:done") { const w = this.waiter; this.waiter = null; clearTimeout(w.timer); setTimeout(() => w.resolve(w.frames), 300); } };
  }); }
  turn(text, capMs = 90_000) { return new Promise((resolve) => {
    const w = { frames: [], resolve, timer: null };
    w.timer = setTimeout(() => { this.waiter = null; resolve(w.frames); }, capMs);
    this.waiter = w; this.ws.send(JSON.stringify({ type: "user", content: text, mode: "efficient" })); }); }
  close() { try { this.ws.close(); } catch {} }
}

const checks = [];
const check = (name, ok, detail) => { checks.push([name, !!ok, detail]); };

async function main() {
  await new Promise((r) => fake.listen(FAKE_PORT, "127.0.0.1", r));
  await fs.mkdir(path.join(PROJECTS, "p", ".tina4-agent", "sessions"), { recursive: true });
  await fs.writeFile(path.join(PROJECTS, "p", ".tina4-agent", "sessions", "gate.json"),
    JSON.stringify({ id: "gate", title: "w20", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));

  boot();
  if (!await upHttp()) { console.log("app did not start"); return 2; }

  const shipped = await get().then((r) => r.json());

  // 1 + 2 — the selection STICKS, for each role independently.
  await post({ thinkerVendor: "custom", thinkerEndpoint: ENDPOINT, thinkerModel: MODEL, thinkerToken: KEY });
  let now = await get().then((r) => r.json());
  check("1 thinker selection sticks", now.thinker?.endpoint === ENDPOINT && now.thinker?.model === MODEL,
        `endpoint=${now.thinker?.endpoint} model=${now.thinker?.model}`);

  await post({ coderVendor: "custom", endpoint: ENDPOINT, model: MODEL, token: KEY });
  now = await get().then((r) => r.json());
  check("2 coder selection sticks", now.endpoint === ENDPOINT && now.model === MODEL,
        `endpoint=${now.endpoint} model=${now.model}`);

  // 3 — the key is never handed back out.
  const raw = await get().then((r) => r.text());
  check("3 no GET ever returns the key", !raw.includes(KEY), raw.includes(KEY) ? "KEY FOUND IN /api/model" : "absent");

  // 4 — wherever the key is stored, it is not world-readable.
  const settingsPath = path.join(STATE, "settings.json");
  const settingsRaw = existsSync(settingsPath) ? readFileSync(settingsPath, "utf8") : "";
  const inSettings = settingsRaw.includes(KEY);
  const settingsMode = existsSync(settingsPath) ? (statSync(settingsPath).mode & 0o777).toString(8) : "-";
  let keyFile = null, keyMode = "-";
  for (const d of [path.join(STATE, "secrets")]) {
    if (!existsSync(d)) continue;
    for (const f of await fs.readdir(d)) {
      const p = path.join(d, f);
      if (readFileSync(p, "utf8").includes(KEY)) { keyFile = p; keyMode = (statSync(p).mode & 0o777).toString(8); }
    }
  }
  // NOT "the key is nowhere" -- that passes on the untouched tree, where no key is stored at all,
  // and it also passes for a build that keeps the key in memory and loses it on restart. The key
  // MUST be somewhere, and that somewhere must not be readable by other users on the machine.
  const storedSomewhere = inSettings || !!keyFile;
  const storedSafely = (!inSettings || settingsMode === "600") && (!keyFile || keyMode === "600");
  check("4 key is persisted, and not world-readable", storedSomewhere && storedSafely,
        `stored=${storedSomewhere} settings.json mode=${settingsMode} holdsKey=${inSettings}; secretFile=${keyFile ? path.basename(keyFile) + " mode=" + keyMode : "none"}`);

  // 5 — a REAL TURN reaches the third party, with the right bearer and the right model. This is the
  // check a stub cannot pass: not "was it saved", but "was it used".
  seen.length = 0;
  const s = new Session("gate"); await s.open();
  await s.turn("what does this project do?");
  s.close();
  const chats = seen.filter((x) => x.kind === "chat");
  const rightAuth = chats.filter((x) => x.auth === `Bearer ${KEY}`);
  const rightModel = chats.filter((x) => x.model === MODEL);
  check("5 a real turn calls the provider with the key", chats.length > 0 && rightAuth.length === chats.length,
        `${chats.length} chat call(s), ${rightAuth.length} with Bearer <key>`);
  check("6 a real turn asks for the chosen model", chats.length > 0 && rightModel.length > 0,
        `models seen: ${[...new Set(chats.map((x) => x.model))].join(", ") || "none"}`);

  // 7 — survives a restart. The second user's first complaint would be "I typed my key twice".
  stop(); await sleep(1500); boot();
  if (!await upHttp()) { check("7 selection survives a restart", false, "app did not come back"); check("8 the KEY survives a restart", false, "app did not come back"); }
  else {
    const re = await get().then((r) => r.json());
    check("7 selection survives a restart", re.thinker?.endpoint === ENDPOINT && re.endpoint === ENDPOINT,
          `thinker=${re.thinker?.endpoint} coder=${re.endpoint}`);
    // Endpoint and model surviving is not enough: a build that persists those two and drops the
    // TOKEN passes check 7 and still makes the user retype their key on every restart. Drive a
    // second turn and look at the wire.
    seen.length = 0;
    const s2 = new Session("gate"); await s2.open();
    await s2.turn("and what language is it in?");
    s2.close();
    const c2 = seen.filter((x) => x.kind === "chat");
    check("8 the KEY survives a restart", c2.length > 0 && c2.every((x) => x.auth === `Bearer ${KEY}`),
          `${c2.length} chat call(s) after restart, auth seen: ${[...new Set(c2.map((x) => x.auth || "(none)"))].join(" | ")}`);
  }

  console.log(`tree     ${TREE}`);
  console.log(`shipped  coder=${shipped.endpoint} thinker=${shipped.thinker?.endpoint} vendors=${(shipped.vendors || []).map((v) => v.id).join(",")}`);
  console.log("");
  for (const [n, ok, d] of checks) console.log(`  ${ok ? "ok  " : "FAIL"}  ${n}\n          ${d}`);
  const pass = checks.every((c) => c[1]);
  console.log(`\n  ${pass ? "PASS" : "FAIL"} — ${checks.filter((c) => c[1]).length}/${checks.length}`);
  return pass ? 0 : 1;
}

let code = 2;
try { code = await main(); } catch (e) { console.log("gate threw:", e.message); code = 2; }
stop(); await sleep(500);
try { fake.close(); } catch {}
await fs.rm(HOME, { recursive: true, force: true });
console.log(`home removed: ${!existsSync(HOME)}`);
process.exit(code);
