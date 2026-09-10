// run-20 -- stage 5. ATTACK THE FIX. Each cell boots its own app against a gateway that reports
// usage in a DIFFERENT shape, and checks what the session counter did with it.
//
//   T4TREE=.../scratch node attack.mjs
//
// The axes: {usage present, absent, zero, malformed, negative, string, total-only, parts-only,
// anthropic-shaped} x {one turn, three turns} x {two sessions in one project}.
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE = process.env.T4TREE || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
let PORT = 8810, GW = 8910;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitHttp(url, tries = 60) { for (let i = 0; i < tries; i++) { try { const r = await fetch(url); if (r.ok) return true; } catch {} await sleep(250); } return false; }

function gateway(port, usageFor) {
  let calls = 0;
  const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
  const srv = http.createServer((req, res) => {
    if (req.method !== "POST") { res.writeHead(404).end(); return; }
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      let b0 = null; try { b0 = JSON.parse(body); } catch {}
      calls++;
      const maxTok = Number(b0?.max_tokens ?? 0);
      const sys = String(b0?.messages?.[0]?.content ?? "");
      const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
        : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
        : "It is a small static page. Nothing is broken.";
      const usage = usageFor(calls);
      const payload = { choices: [{ message: { role: "assistant", content: answer } }] };
      if (usage !== undefined) payload.usage = usage;
      if (b0 && b0.stream === false) { res.writeHead(200, { "content-type": "application/json" }); res.end(JSON.stringify(payload)); return; }
      res.writeHead(200, { "content-type": "text/event-stream" });
      sse(res, { choices: [{ delta: { role: "assistant" } }] });
      sse(res, { choices: [{ delta: { content: answer } }] });
      sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
      if (usage !== undefined) sse(res, { choices: [], usage });
      res.write("data: [DONE]\n\n"); res.end();
    });
  });
  return { srv, calls: () => calls };
}

class Session {
  constructor(port, project, sid) { Object.assign(this, { port, project, sid }); this.waiter = null; }
  open() { return new Promise((resolve) => {
    this.ws = new WebSocket(`ws://127.0.0.1:${this.port}/ws/agent`);
    this.ws.onopen = () => { this.ws.send(JSON.stringify({ type: "session:activate", id: this.sid, project: this.project })); setTimeout(resolve, 600); };
    this.ws.onmessage = (ev) => { let m; try { m = JSON.parse(ev.data); } catch { return; }
      if (!this.waiter) return;
      this.waiter.frames.push(m);
      if (m.type === "turn:done") { const w = this.waiter; this.waiter = null; clearTimeout(w.timer); setTimeout(() => w.resolve(w.frames), 300); } };
  }); }
  turn(text, capMs = 60000) { return new Promise((resolve) => {
    const w = { frames: [], resolve, timer: null };
    w.timer = setTimeout(() => { this.waiter = null; resolve(w.frames); }, capMs);
    this.waiter = w; this.ws.send(JSON.stringify({ type: "user", content: text, mode: "efficient" }));
  }); }
  close() { try { this.ws.close(); } catch {} }
}

async function withApp(usageFor, fn) {
  const port = PORT++, gwPort = GW++;
  const PROJECTS = path.join(os.tmpdir(), `t4a-atk-${process.pid}-${port}`);
  const STATE = path.join(os.tmpdir(), `t4a-atks-${process.pid}-${port}`);
  const g = gateway(gwPort, usageFor);
  await new Promise((r) => g.srv.listen(gwPort, "127.0.0.1", r));
  const seed = async (proj, sid) => { const d = path.join(PROJECTS, proj, ".tina4-agent", "sessions"); await fs.mkdir(d, { recursive: true });
    await fs.writeFile(path.join(d, `${sid}.json`), JSON.stringify({ id: sid, title: sid, status: "active", createdAt: 1, updatedAt: 1, messages: [] })); };
  await seed("p", "a"); await seed("p", "b");
  const app = spawn("npx", ["tsx", "app.ts"], { cwd: TREE, detached: true,
    env: { ...process.env, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(port), TINA4_STATE_DIR: STATE,
      TINA4_MODEL_ENDPOINT: `http://127.0.0.1:${gwPort}/v1`, TINA4_MODEL_ID: "fake", TINA4_MODEL_TOKEN: "t",
      TINA4_THINKER_ENDPOINT: `http://127.0.0.1:${gwPort}/v1`, TINA4_THINKER_MODEL: "fake", TINA4_THINKER_TOKEN: "t",
      TINA4_THINKING_MODE: "false", TINA4_THINKER_PLAN: "0",
      TINA4_PROJECTS_ROOT: PROJECTS, TINA4_CURRENT_PROJECT: "p", TINA4_DEBUG: "false", TINA4_NO_BROWSER: "1" },
    stdio: ["ignore", "ignore", "ignore"] });
  try {
    if (!await waitHttp(`http://127.0.0.1:${port}/api/model`)) throw new Error("app did not start");
    const read = async (sid) => JSON.parse(await fs.readFile(path.join(PROJECTS, "p", ".tina4-agent", "sessions", `${sid}.json`), "utf8"));
    return await fn({ port, read, calls: g.calls });
  } finally {
    try { process.kill(-app.pid, "SIGTERM"); } catch {}
    await new Promise((r) => g.srv.close(r));
    await fs.rm(PROJECTS, { recursive: true, force: true }).catch(() => {});
    await fs.rm(STATE, { recursive: true, force: true }).catch(() => {});
  }
}

const results = [];
const check = (name, ok, detail = "") => { results.push({ name, ok }); console.log(`${ok ? "  ok  " : "  FAIL"} ${name}${ok ? "" : "  -- " + detail}`); };

// --- cell 1: exact arithmetic, and turn:done reports THIS turn, not the running total.
await withApp(() => ({ prompt_tokens: 90, completion_tokens: 10, total_tokens: 100 }), async ({ port, read, calls }) => {
  const s = new Session(port, "p", "a"); await s.open();
  const perTurn = [];
  for (let i = 0; i < 3; i++) {
    const before = calls();
    const fr = await s.turn("what is this project? " + i);
    const done = fr.filter((f) => f.type === "turn:done").pop();
    perTurn.push({ spent: (calls() - before) * 100, frameTokens: done?.tokens, frameTotal: done?.totalTokens });
  }
  s.close();
  const sess = await read("a");
  const expected = calls() * 100;
  console.log("   ", JSON.stringify(perTurn), " session:", sess.totalTokens, " gateway total:", expected);
  check("session total == every token the gateway reported", sess.totalTokens === expected, `${sess.totalTokens} vs ${expected}`);
  check("turn:done tokens = THAT turn only, not cumulative", perTurn.every((t) => t.frameTokens === t.spent), JSON.stringify(perTurn));
  check("totalTokens is monotonic across turns", perTurn.map((t) => t.frameTotal).every((v, i, a) => i === 0 || v > a[i - 1]), JSON.stringify(perTurn.map((t) => t.frameTotal)));
});

// --- cell 2: the second user. A gateway that reports NO usage at all must leave the counter at 0
//     and must not poison it with NaN -- a NaN here would persist to JSON as null and break the UI.
await withApp(() => undefined, async ({ port, read }) => {
  const s = new Session(port, "p", "a"); await s.open(); await s.turn("what is this?"); s.close();
  const sess = await read("a");
  check("no usage reported -> counter stays 0, not NaN/null", sess.totalTokens === 0, JSON.stringify(sess.totalTokens));
  check("elapsed still recorded when usage is absent", Number(sess.totalElapsedMs) > 0, JSON.stringify(sess.totalElapsedMs));
});

// --- cell 3: malformed usage. Strings, nulls, negatives, garbage. None may reach the counter.
await withApp((n) => [
  { total_tokens: "120" },                       // numeric string
  { total_tokens: null },
  { total_tokens: -500 },                        // negative: must never subtract
  { total_tokens: NaN },
  { prompt_tokens: "x", completion_tokens: {} }, // nonsense
  {},                                            // empty object
][n % 6], async ({ port, read }) => {
  const s = new Session(port, "p", "a"); await s.open();
  for (let i = 0; i < 3; i++) await s.turn("what is this? " + i);
  s.close();
  const sess = await read("a");
  const v = sess.totalTokens;
  check("malformed usage never yields NaN or a negative", Number.isFinite(v) && v >= 0, JSON.stringify(v));
  check('a numeric string "120" is still counted, garbage is not', v > 0, JSON.stringify(v));
});

// --- cell 4: parts only, no total_tokens (a gateway that omits the sum).
await withApp(() => ({ prompt_tokens: 40, completion_tokens: 60 }), async ({ port, read, calls }) => {
  const s = new Session(port, "p", "a"); await s.open(); await s.turn("what is this?"); s.close();
  const sess = await read("a");
  check("prompt+completion used when total_tokens is missing", sess.totalTokens === calls() * 100, `${sess.totalTokens} vs ${calls() * 100}`);
});

// --- cell 5: Anthropic-shaped usage (input_tokens/output_tokens). We do NOT guess -- but it must
//     not corrupt the counter either. Documents the gap rather than pretending it is handled.
await withApp(() => ({ input_tokens: 500, output_tokens: 500 }), async ({ port, read }) => {
  const s = new Session(port, "p", "a"); await s.open(); await s.turn("what is this?"); s.close();
  const sess = await read("a");
  check("anthropic-shaped usage is ignored cleanly (known gap, not a crash)", sess.totalTokens === 0, JSON.stringify(sess.totalTokens));
});

// --- cell 6: two sessions in one project must not share a counter.
await withApp(() => ({ total_tokens: 100 }), async ({ port, read }) => {
  const a = new Session(port, "p", "a"); await a.open(); await a.turn("first"); await a.turn("second"); a.close();
  const b = new Session(port, "p", "b"); await b.open(); await b.turn("only one here"); b.close();
  const [sa, sb] = [await read("a"), await read("b")];
  check("per-session counters are independent", sa.totalTokens > sb.totalTokens && sb.totalTokens > 0, `a=${sa.totalTokens} b=${sb.totalTokens}`);
});

console.log("");
const bad = results.filter((r) => !r.ok);
console.log(bad.length ? `  ${bad.length} of ${results.length} FAILED` : `  all ${results.length} clean`);
const left = (await fs.readdir(os.tmpdir())).filter((d) => d.startsWith(`t4a-atk`) && d.includes(String(process.pid)));
console.log(left.length ? "  CLEANUP FAILED: " + left.join(" ") : "  cleanup verified: no throwaway dirs left");
process.exit(bad.length ? 1 : 0);
