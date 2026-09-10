// run-20 -- REPRODUCTION. Does a session's token counter ever move off zero?
//
// Michael, 2026-09-08: "tokens used in my last session when i swapped thinker to claude said 0
// tokens." All four of his real Tempooo sessions read totalTokens: 0 with a correct
// totalElapsedMs. This drives the SAME path offline, against a fake OpenAI gateway that reports
// usage on every single call, so the tokens are unambiguously available to the app.
//
//   T4TREE=/var/home/work/gitdir/tina4-simple-agent-work/baseline-main node repro.mjs
//
// Prints, per turn: what the gateway reported, what the turn:done frame carried, and what landed
// in the persisted session JSON. Exit 1 if the counter stayed at zero (the defect), 0 if it moved.
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE = process.env.T4TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const FAKE_PORT = Number(process.env.FAKE_PORT || 8899);
const APP_PORT = Number(process.env.APP_PORT || 8791);
const PROJECTS = path.join(os.tmpdir(), "t4a-run20-" + process.pid);
const STATE = path.join(os.tmpdir(), "t4a-run20-state-" + process.pid);
const TOKENS_PER_CALL = 137;   // deliberately not a round number, so it cannot be confused with a default

// ---- fake gateway: same shape as test/turn-harness.mjs, but it TALLIES what it hands out.
let served = { streaming: 0, nonStreaming: 0, tokensReported: 0 };
const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
const fake = http.createServer((req, res) => {
  if (req.method !== "POST") { res.writeHead(404).end(); return; }
  let body = ""; req.on("data", (c) => (body += c));
  req.on("end", () => {
    let b0 = null; try { b0 = JSON.parse(body); } catch {}
    const maxTok = Number(b0?.max_tokens ?? 0);
    const sysMsg = String(b0?.messages?.[0]?.content ?? "");
    // The app probes intent with max_tokens<=8 and expects ONE word back. Anything else (or an empty
    // 200) is read as an offline stub and the turn opens Setup instead of running -- which is how the
    // first draft of this probe ended up measuring a turn that had already given up.
    const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
      : /\bJSON\b/i.test(sysMsg) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
      : "It is a small static page. Nothing is broken.";
    if (b0 && b0.stream === false) {
      served.nonStreaming++; served.tokensReported += TOKENS_PER_CALL;
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }],
        usage: { prompt_tokens: 100, completion_tokens: 37, total_tokens: TOKENS_PER_CALL } }));
      return;
    }
    served.streaming++; served.tokensReported += TOKENS_PER_CALL;
    res.writeHead(200, { "content-type": "text/event-stream" });
    sse(res, { choices: [{ delta: { role: "assistant" } }] });
    sse(res, { choices: [{ delta: { content: answer } }] });
    sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
    sse(res, { choices: [], usage: { prompt_tokens: 100, completion_tokens: 37, total_tokens: TOKENS_PER_CALL } });
    res.write("data: [DONE]\n\n"); res.end();
  });
});

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitHttp(url, tries = 60) {
  for (let i = 0; i < tries; i++) { try { const r = await fetch(url); if (r.ok) return true; } catch {} await sleep(250); }
  return false;
}
async function seedSession(project, sid) {
  const dir = path.join(PROJECTS, project, ".tina4-agent", "sessions");
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, `${sid}.json`),
    JSON.stringify({ id: sid, title: "run20", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));
}
async function readSession(project, sid) {
  try { return JSON.parse(await fs.readFile(path.join(PROJECTS, project, ".tina4-agent", "sessions", `${sid}.json`), "utf8")); }
  catch (e) { return { readError: String(e) }; }
}
// ONE socket for the whole run. A second WebSocket would re-attach and REPLAY the buffered
// frames of the previous turn -- including its turn:done -- and an earlier draft of this probe
// took that replay for turn 2's result and reported "0 model calls" for a turn it never sent.
// Capped: a turn that never closes is a NAMED failure, never a wedged run.
class Session {
  constructor(project, sid) { this.project = project; this.sid = sid; this.ws = null; this.waiter = null; }
  open() {
    return new Promise((resolve) => {
      this.ws = new WebSocket(`ws://127.0.0.1:${APP_PORT}/ws/agent`);
      this.ws.onopen = () => { this.ws.send(JSON.stringify({ type: "session:activate", id: this.sid, project: this.project })); setTimeout(resolve, 600); };
      this.ws.onmessage = (ev) => {
        let m; try { m = JSON.parse(ev.data); } catch { return; }
        if (!this.waiter) return;                      // frames before a turn was asked for = replay//chatter
        this.waiter.frames.push(m);
        if (m.type === "turn:done") { const w = this.waiter; this.waiter = null; clearTimeout(w.timer); setTimeout(() => w.resolve({ frames: w.frames, timedOut: false }), 300); }
      };
    });
  }
  turn(text, capMs = 90000) {
    return new Promise((resolve) => {
      const w = { frames: [], resolve, timer: null };
      w.timer = setTimeout(() => { this.waiter = null; resolve({ frames: w.frames, timedOut: true }); }, capMs);
      this.waiter = w;
      this.ws.send(JSON.stringify({ type: "user", content: text, mode: "efficient" }));
    });
  }
  close() { try { this.ws.close(); } catch {} }
}

let app = null;
async function main() {
  await new Promise((r) => fake.listen(FAKE_PORT, "127.0.0.1", r));
  await fs.mkdir(PROJECTS, { recursive: true });
  app = spawn("npx", ["tsx", "app.ts"], {
    cwd: TREE, detached: true,
    env: { ...process.env,
      TINA4_HOST: "127.0.0.1",
      TINA4_AGENT_PORT: String(APP_PORT),
      TINA4_STATE_DIR: STATE,
      TINA4_MODEL_ENDPOINT: `http://127.0.0.1:${FAKE_PORT}/v1`,
      TINA4_MODEL_ID: "fake-model", TINA4_MODEL_TOKEN: "test",
      TINA4_THINKER_ENDPOINT: `http://127.0.0.1:${FAKE_PORT}/v1`,
      TINA4_THINKER_MODEL: "fake-model", TINA4_THINKER_TOKEN: "test",
      TINA4_THINKING_MODE: "false", TINA4_THINKER_PLAN: "0",
      TINA4_PROJECTS_ROOT: PROJECTS, TINA4_CURRENT_PROJECT: "p",
      TINA4_DEBUG: "false", TINA4_NO_BROWSER: "1" },
    stdio: ["ignore", "ignore", "pipe"],
  });
  let stderr = ""; app.stderr.on("data", (c) => { stderr += c; });

  if (!await waitHttp(`http://127.0.0.1:${APP_PORT}/api/model`)) {
    console.error("app did not start from", TREE);
    console.error(stderr.slice(-2000));
    return 2;
  }
  console.log("  tree              ", TREE);
  console.log("  gateway reports   ", `usage.total_tokens = ${TOKENS_PER_CALL} on EVERY call`);
  console.log("");

  const P = "p", SID = "run20";
  await seedSession(P, SID);
  const sess0 = new Session(P, SID);
  await sess0.open();

  const rows = [];
  for (const [n, msg] of [[1, "say hi"], [2, "say hi again"]]) {
    const before = { ...served };
    const { frames, timedOut } = await sess0.turn(msg);
    const done = frames.filter((f) => f.type === "turn:done").pop() || null;
    const sess = await readSession(P, SID);
    rows.push({
      turn: n, timedOut,
      callsThisTurn: (served.streaming + served.nonStreaming) - (before.streaming + before.nonStreaming),
      tokensGatewayReported: served.tokensReported - before.tokensReported,
      frameTokens: done ? done.tokens : "(no turn:done)",
      frameTotalTokens: done ? done.totalTokens : "(no turn:done)",
      frameTotalElapsedMs: done ? done.totalElapsedMs : "(no turn:done)",
      sessionTotalTokens: sess.totalTokens,
      sessionTotalElapsedMs: sess.totalElapsedMs,
      frameTypes: frames.map((f) => f.type).join(","),
    });
  }
  sess0.close();
  console.table(rows.map(({frameTypes,...r})=>r));
  rows.forEach((r)=>console.log("  turn",r.turn,"frames:",r.frameTypes.slice(0,300)));

  const cumulativeGateway = served.tokensReported;
  const last = rows[rows.length - 1];
  console.log("");
  console.log("  gateway handed out       ", cumulativeGateway, "tokens across", served.streaming + served.nonStreaming, "calls");
  console.log("  session recorded         ", JSON.stringify(last.sessionTotalTokens));
  console.log("  session elapsed recorded ", JSON.stringify(last.sessionTotalElapsedMs), "ms   <- the control: this one works");
  console.log("");

  const anyTimeout = rows.some((r) => r.timedOut);
  if (anyTimeout) { console.log("  INCONCLUSIVE - a turn hit its cap, so nothing here is a clean measurement"); return 2; }
  const counterMoved = Number(last.sessionTotalTokens) > 0;
  if (counterMoved) { console.log("  counter MOVED - defect not reproduced on this tree"); return 0; }
  console.log("  counter STUCK AT ZERO while elapsed time accumulated - defect reproduced");
  return 1;
}

let code = 2;
try { code = await main(); }
catch (e) { console.error("probe error:", e); code = 2; }
finally {
  try { if (app && app.pid) process.kill(-app.pid, "SIGTERM"); } catch {}
  await new Promise((r) => fake.close(r));
  await fs.rm(PROJECTS, { recursive: true, force: true }).catch(() => {});
  await fs.rm(STATE, { recursive: true, force: true }).catch(() => {});
  // Verified, not assumed: say out loud whether the throwaway dirs are actually gone.
  const left = [];
  for (const d of [PROJECTS, STATE]) { try { await fs.stat(d); left.push(d); } catch {} }
  console.log(left.length ? "  CLEANUP FAILED, still present: " + left.join(" ") : "  cleanup verified: throwaway dirs gone");
}
process.exit(code);
