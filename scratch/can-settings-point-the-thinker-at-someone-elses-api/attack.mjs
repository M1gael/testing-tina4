// w-20 ATTACK -- gate.mjs proves the cases I thought of while designing. This visits the cells I
// did not: the SECOND user. They have a settings.json written before this feature existed, a
// half-filled form, two providers instead of one, and a key with a space on the end from a paste.
//
// Cells are stated as the wrong thing they would catch, not as "it works".
//
//   T4_TREE=<tree> node attack.mjs        exit 0 = nothing got through
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import { existsSync, statSync, readFileSync, chmodSync } from "node:fs";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const APP_PORT = Number(process.env.T4_PORT || 8798);
const A_PORT = Number(process.env.T4_A_PORT || 8903);   // the coder's provider
const B_PORT = Number(process.env.T4_B_PORT || 8904);   // the thinker's provider -- a DIFFERENT one
const KEY_A = "sk-AAA-coderkey-1111";
const KEY_B = "sk-BBB-thinkerkey-2222";
const MODEL_A = "deepseek/deepseek-chat";
const MODEL_B = "deepseek-reasoner";
const HOME = path.join(os.tmpdir(), "w20-attack-" + process.pid);
const STATE = path.join(HOME, ".tina4-simple-agent");
const PROJECTS = path.join(HOME, "projects");
const SETTINGS = path.join(STATE, "settings.json");

// ---- two third parties, each recording what reached IT specifically.
const seenA = [], seenB = [];
const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
function provider(seen, model, key) {
  return http.createServer((req, res) => {
    if (req.method === "GET") {
      seen.push({ kind: "models", auth: req.headers.authorization || "" });
      // A real provider refuses a wrong key. Without that, "Test" cannot be shown to fail.
      if (key && req.headers.authorization !== `Bearer ${key}`) {
        res.writeHead(401, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: { message: "Incorrect API key provided" } })); return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ data: [{ id: model, context_window: 64000 }] })); return;
    }
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      let b = null; try { b = JSON.parse(body); } catch {}
      seen.push({ kind: "chat", auth: req.headers.authorization || "", model: b?.model });
      const maxTok = Number(b?.max_tokens ?? 0);
      const sys = String(b?.messages?.[0]?.content ?? "");
      const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
        : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
        : "It is a small static page. Nothing is broken.";
      if (b && b.stream === false) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }],
          usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } })); return;
      }
      res.writeHead(200, { "content-type": "text/event-stream" });
      sse(res, { choices: [{ delta: { role: "assistant" } }] });
      sse(res, { choices: [{ delta: { content: answer } }] });
      sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
      sse(res, { choices: [], usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } });
      res.write("data: [DONE]\n\n"); res.end();
    });
  });
}
const A = provider(seenA, MODEL_A, KEY_A), B = provider(seenB, MODEL_B, KEY_B);
const EP_A = `http://127.0.0.1:${A_PORT}/v1`, EP_B = `http://127.0.0.1:${B_PORT}/v1`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let app = null;
function boot() {
  app = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
    cwd: TREE, detached: true, stdio: ["ignore", "ignore", "pipe"],
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
const mode = (p) => (existsSync(p) ? (statSync(p).mode & 0o777).toString(8) : "-");

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

const cells = [];
// A cell that cannot run is a FAILURE, never a skip -- an unrunnable cell once passed this suite
// on `undefined === undefined`.
const cell = (name, ok, detail) => { cells.push([name, ok === true, detail ?? ""]); };

async function main() {
  await new Promise((r) => A.listen(A_PORT, "127.0.0.1", r));
  await new Promise((r) => B.listen(B_PORT, "127.0.0.1", r));
  await fs.mkdir(path.join(PROJECTS, "p", ".tina4-agent", "sessions"), { recursive: true });
  await fs.writeFile(path.join(PROJECTS, "p", ".tina4-agent", "sessions", "atk.json"),
    JSON.stringify({ id: "atk", title: "w20 attack", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));

  // ---- 1. A settings.json written BEFORE this feature existed. No coderVendor, no thinkerVendor,
  // mode 0644, and a token already in it. Migration: it must load, and the first save must tighten it.
  await fs.mkdir(STATE, { recursive: true });
  await fs.writeFile(SETTINGS, JSON.stringify({
    actorName: "Old Build", endpoint: "https://mcp.tina4.com/v1", model: "tina4-coder",
    token: "FREE-TOKEN", thinkerEndpoint: "https://mcp.tina4.com/v1", thinkerModel: "tina4-thinker",
    thinkerToken: "FREE-TOKEN", autoPilot: false,
  }, null, 2));
  chmodSync(SETTINGS, 0o644);
  const modeBefore = mode(SETTINGS);

  boot();
  if (!await upHttp()) { cell("1 an OLD settings.json still loads", false, "app did not start at all"); return report(); }
  const first = await get().then((r) => r.json()).catch(() => null);
  cell("1 an OLD settings.json still loads", !!first && first.model === "tina4-coder",
       `model=${first?.model} coderVendor=${first?.coderVendor ?? "(absent)"}`);

  // ---- 2. Nothing has been typed yet. The Custom row must NOT claim to be connected -- least of
  // all to mcp.tina4.com, whose URL and FREE-TOKEN are sitting in the very fields it reads.
  const customRow = (j) => (j.vendors || []).find((v) => v.id === "custom");
  const c0 = customRow(first);
  cell("2 Custom does not claim to be connected before anything is typed",
       !!c0 && c0.status !== "connected",
       `status=${c0?.status} account=${c0?.account ?? "-"} reason=${c0?.reason ?? "-"}`);

  // ---- 3. Half a form. Endpoint given, key not. Must not crash, must not read as ready.
  await post({ coderVendor: "custom", endpoint: EP_A, model: MODEL_A, token: "" });
  const half = await get().then((r) => r.json());
  // The row must EXIST and not be connected. "?.status !== connected" alone is satisfied by
  // undefined, which is how a tree with no custom vendor at all passed this cell.
  cell("3 half a form is not 'connected'",
       !!customRow(half) && customRow(half).status !== "connected",
       `status=${customRow(half)?.status ?? "(no custom vendor at all)"} reason=${customRow(half)?.reason ?? "-"}`);

  // ---- 4. MIXED roles. Coder on someone else's API, thinker still on the gateway. The two must not
  // overwrite each other -- this is exactly what reconcileVendorWiring() exists to do.
  await post({ coderVendor: "custom", endpoint: EP_A, model: MODEL_A, token: KEY_A });
  await post({ thinkerVendor: "tina4", thinkerVendorModel: "tina4-thinker" });
  const mixed = await get().then((r) => r.json());
  cell("4 a custom coder survives a tina4 thinker beside it",
       mixed.endpoint === EP_A && /mcp\.tina4\.com/.test(String(mixed.thinker?.endpoint)),
       `coder=${mixed.endpoint} thinker=${mixed.thinker?.endpoint}`);

  // ---- 5. TWO different providers at once, different keys. The keys must not cross.
  await post({ thinkerVendor: "custom", thinkerEndpoint: EP_B, thinkerModel: MODEL_B, thinkerToken: KEY_B });
  const both = await get().then((r) => r.json());
  cell("5 two custom providers keep their own endpoints",
       both.endpoint === EP_A && both.thinker?.endpoint === EP_B,
       `coder=${both.endpoint} thinker=${both.thinker?.endpoint}`);

  // ---- 11. The POSITIVE side of cell 2. A status that is never "connected" would pass cells 2 and
  // 3 while telling a correctly-configured user their provider is not set up.
  cell("11 a fully configured Custom reads as connected, and names the host",
       customRow(both)?.status === "connected" && String(customRow(both)?.account || "").includes("127.0.0.1"),
       `status=${customRow(both)?.status} account=${customRow(both)?.account ?? "-"}`);

  // ---- 12. The model the cost ledger names must be the one the user typed, not whichever tina4
  // model was selected before they switched. The old settings.json above left "tina4-coder" behind.
  cell("12 the reported vendor model is the typed one, not the stale tina4 one",
       both.coderVendorModel === MODEL_A && both.thinkerVendorModel === MODEL_B,
       `coderVendorModel=${both.coderVendorModel} thinkerVendorModel=${both.thinkerVendorModel}`);

  // Both roles are exercised, but NOT by assuming one turn uses both. A question turn is answered by
  // the thinker alone -- the first version of this cell demanded a coder chat during a question and
  // read the coder's silence as a broken build. What each role's wiring must do is reach ITS OWN
  // provider with ITS OWN key: POST /api/model probes both endpoints (app.ts:2015), and a turn
  // drives whichever role the turn needs. Assert over every request either provider received.
  seenA.length = 0; seenB.length = 0;
  await post({});                                   // triggers the pair of /models probes
  await sleep(1200);
  const s = new Session("atk"); await s.open();
  await s.turn("what does this project do?");
  s.close();
  const aChats = seenA.filter((x) => x.kind === "chat"), bChats = seenB.filter((x) => x.kind === "chat");
  const crossed = [...seenA.filter((x) => x.auth.includes(KEY_B)), ...seenB.filter((x) => x.auth.includes(KEY_A))];
  cell("6 neither provider is ever sent the other's key",
       crossed.length === 0 && seenA.length > 0 && seenB.length > 0,
       `A saw ${seenA.length} request(s) (${aChats.length} chat), B saw ${seenB.length} (${bChats.length} chat); crossed=${crossed.length}`);
  const aOwn = seenA.length > 0 && seenA.every((x) => x.auth === `Bearer ${KEY_A}`);
  const bOwn = seenB.length > 0 && seenB.every((x) => x.auth === `Bearer ${KEY_B}`);
  cell("7 each role reached its own provider under its own key", aOwn && bOwn,
       `A auth=${[...new Set(seenA.map((x) => x.auth))].join("|") || "NOTHING REACHED A"}  B auth=${[...new Set(seenB.map((x) => x.auth))].join("|") || "NOTHING REACHED B"}`);

  // ---- 8. A pasted key almost always carries whitespace. It must not reach the wire with it --
  // "Bearer sk-x " is a 401 the user cannot see the cause of.
  seenA.length = 0;
  await post({ coderVendor: "custom", endpoint: EP_A, model: MODEL_A, token: `  ${KEY_A}\n` });
  const s2 = new Session("atk"); await s2.open();
  await s2.turn("and what language is it in?");
  s2.close();
  const auths = [...new Set(seenA.map((x) => x.auth))].filter(Boolean);
  cell("8 a pasted key is not sent with its whitespace",
       auths.length > 0 && auths.every((a) => a === `Bearer ${KEY_A}`),
       `auth seen: ${auths.map((a) => JSON.stringify(a)).join(", ") || "NOTHING REACHED THE PROVIDER"}`);

  // ---- 9. PROPERTY, not an example: no GET the UI makes may contain either key. One assertion
  // over every GET route beats another handful of cases.
  // EVERY GET route the app defines, not a selection -- a negative over an unstated scope is not a
  // finding. `grep -ao 'get("/api/[a-z-]*"' app.ts | sort -u` is where this list comes from; four of
  // them (branches, file, service, tree) need parameters and will answer with an error, which cannot
  // leak a key either and is still worth asking.
  const ROUTES = ["/api/model", "/api/actor", "/api/projects", "/api/project", "/api/sessions",
                  "/api/threads", "/api/secrets", "/api/global-secrets", "/api/doctor", "/api/skills",
                  "/api/branches", "/api/file", "/api/service", "/api/tree"];
  const leaks = [];
  for (const r of ROUTES) {
    try {
      const t = await fetch(`http://127.0.0.1:${APP_PORT}${r}`).then((x) => x.text());
      if (t.includes(KEY_A) || t.includes(KEY_B)) leaks.push(r);
    } catch { /* a route that refuses to answer cannot leak */ }
  }
  // Only meaningful once the app is actually HOLDING a key -- on a tree that never accepted one,
  // "no route returns it" is true and says nothing.
  const holdsAKey = both.endpoint === EP_A && both.thinker?.endpoint === EP_B;
  cell("9 no GET route returns either key", holdsAKey && leaks.length === 0,
       !holdsAKey ? "VACUOUS — the app never accepted a custom provider, so it holds no key to leak"
                  : leaks.length ? `LEAKED BY ${leaks.join(", ")}` : `${ROUTES.length} routes checked, none leaked`);

  // ---- 10. The file the keys landed in was 0644 before this build touched it. It must not still be.
  const settingsNow = existsSync(SETTINGS) ? readFileSync(SETTINGS, "utf8") : "";
  cell("10 an inherited 0644 settings.json is tightened once a key is in it",
       settingsNow.includes(KEY_A) && mode(SETTINGS) === "600",
       `was ${modeBefore}, now ${mode(SETTINGS)}, holds the key=${settingsNow.includes(KEY_A)}`);

  // ---- 13 + 14. "Test" — part (e) of this feature's gate in FEATURES.md: a wrong key must fail IN
  // SETTINGS, not three rounds into a build, and testing must not change what is saved.
  const before = await get().then((r) => r.text());
  const bad = await fetch(`http://127.0.0.1:${APP_PORT}/api/model/test`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ role: "coder", endpoint: EP_A, model: MODEL_A, token: "sk-WRONG-0000" }),
  }).then((r) => r.json()).catch((e) => ({ ok: null, error: String(e) }));
  const afterBad = await get().then((r) => r.text());
  cell("13 Test with a wrong key fails, and changes nothing",
       bad?.ok === false && /401/.test(String(bad.status ?? bad.error ?? "")) && before === afterBad,
       `ok=${bad?.ok} status=${bad?.status ?? "-"} detail=${JSON.stringify(String(bad?.detail ?? bad?.error ?? "").slice(0, 60))} settings unchanged=${before === afterBad}`);

  const good = await fetch(`http://127.0.0.1:${APP_PORT}/api/model/test`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ role: "thinker", endpoint: EP_B, model: MODEL_B, token: KEY_B }),
  }).then((r) => r.json()).catch((e) => ({ ok: null, error: String(e) }));
  cell("14 Test with the right key succeeds and names the model",
       good?.ok === true && good?.modelKnown === true && String(good?.detail || "").includes(MODEL_B),
       `ok=${good?.ok} modelKnown=${good?.modelKnown} detail=${JSON.stringify(String(good?.detail ?? good?.error ?? ""))}`);

  // ---- 15. The Test endpoint must not become a way to read the stored key. It is `.noAuth()` like
  // every route here, and it falls back to the SAVED key when the caller sends a blank one -- so the
  // pair (an endpoint the caller names, no token) would post the user's OpenRouter/DeepSeek key to a
  // host of the caller's choosing, with no user action and nothing shown in the UI.
  const sinkSaw = [];
  const sinkSrv = http.createServer((req, res) => {
    sinkSaw.push(req.headers.authorization || "");
    res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify({ data: [] }));
  });
  const SINK_PORT = A_PORT + 40;
  await new Promise((r) => sinkSrv.listen(SINK_PORT, "127.0.0.1", r));
  const sneak = await fetch(`http://127.0.0.1:${APP_PORT}/api/model/test`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ role: "coder", endpoint: `http://127.0.0.1:${SINK_PORT}/v1`, model: "", token: "" }),
  }).then((r) => r.json()).catch((e) => ({ ok: null, error: String(e) }));
  await sleep(300);
  sinkSrv.close();
  const leakedKey = sinkSaw.some((a) => a.includes(KEY_A) || a.includes(KEY_B));
  cell("15 Test will not send the stored key to an endpoint the caller names",
       !leakedKey,
       leakedKey ? `LEAKED — the sink received ${JSON.stringify(sinkSaw.find((a) => a.includes(KEY_A) || a.includes(KEY_B)))}`
                 : `sink saw ${sinkSaw.length} request(s), none carrying a stored key; reply ok=${sneak?.ok} ${JSON.stringify(String(sneak?.error ?? "").slice(0, 70))}`);

  return report();
}

function report() {
  const w = Math.max(...cells.map((c) => c[0].length));
  console.log();
  for (const [n, ok, d] of cells) console.log(`  ${ok ? "ok  " : "FAIL"}  ${n.padEnd(w)}  ${d}`);
  const bad = cells.filter((c) => !c[1]).length;
  console.log(`\n  ${bad ? "FAIL" : "PASS"} — ${cells.length - bad}/${cells.length}\n`);
  return bad ? 1 : 0;
}

let code = 2;
try { code = await main(); } catch (e) { console.log("attack threw: " + (e?.stack || e)); code = 2; }
stop(); await sleep(600);
try { A.close(); B.close(); } catch {}
await fs.rm(HOME, { recursive: true, force: true }).catch(() => {});
console.log(`  tmp removed: ${existsSync(HOME) ? "NO" : "yes"}`);
process.exit(code);
