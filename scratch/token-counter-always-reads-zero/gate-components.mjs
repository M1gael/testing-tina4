// run-20 -- stage 5, component gating. Two SEPARATE gateways (thinker 1000 tokens/call, coder 7)
// so the session counter's arithmetic says which model contributed. Drives the paths the earlier
// cells never reached: the STREAMING thinker (chat lane) and the CODER (build lane).
//
//   T4TREE=.../scratch node gate-components.mjs
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE = process.env.T4TREE || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const INTENT = process.env.T4_INTENT || "CHAT";
const THINKER_TOK = 1000, CODER_TOK = 7;
const PORT = Number(process.env.APP_PORT || 8830), TGW = 8930, CGW = 8931;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitHttp(u, n = 60) { for (let i = 0; i < n; i++) { try { const r = await fetch(u); if (r.ok) return true; } catch {} await sleep(250); } return false; }

const PAGE = "<!doctype html><html><head><title>t</title></head><body><h1>hello</h1><script>console.log(1)</script></body></html>";
const seen = { thinker: { json: 0, sse: 0 }, coder: { json: 0, sse: 0 } };
function gw(role, tokens) {
  const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
  return http.createServer((req, res) => {
    if (req.method !== "POST") { res.writeHead(404).end(); return; }
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      let b0 = null; try { b0 = JSON.parse(body); } catch {}
      const maxTok = Number(b0?.max_tokens ?? 0);
      const sys = String(b0?.messages?.[0]?.content ?? "");
      const answer = role === "coder" ? PAGE
        : maxTok > 0 && maxTok <= 8 ? INTENT
        : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
        : "Sure -- it is a small static page and nothing looks broken.";
      const usage = { prompt_tokens: Math.floor(tokens * 0.8), completion_tokens: tokens - Math.floor(tokens * 0.8), total_tokens: tokens };
      if (b0 && b0.stream === false) { seen[role].json++; res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }], usage })); return; }
      seen[role].sse++;
      res.writeHead(200, { "content-type": "text/event-stream" });
      // T4_REPEAT_USAGE mimics a gateway that puts the usage block on EVERY chunk instead of once.
      // The count must not multiply by the number of chunks.
      const rep = process.env.T4_REPEAT_USAGE && b0?.stream_options?.include_usage ? usage : undefined;
      sse(res, { choices: [{ delta: { role: "assistant" } }], ...(rep ? { usage: rep } : {}) });
      sse(res, { choices: [{ delta: { content: answer } }], ...(rep ? { usage: rep } : {}) });
      sse(res, { choices: [{ delta: {}, finish_reason: "stop" }], ...(rep ? { usage: rep } : {}) });
      // usage on a stream is sent ONLY when the client asked via stream_options.include_usage --
      // mirroring the real gateway, so a fix that forgets to ask gets nothing here.
      if (b0?.stream_options?.include_usage) sse(res, { choices: [], usage });
      res.write("data: [DONE]\n\n"); res.end();
    });
  });
}
const tSrv = gw("thinker", THINKER_TOK), cSrv = gw("coder", CODER_TOK);

class Session {
  constructor(port, project, sid) { Object.assign(this, { port, project, sid }); this.waiter = null; }
  open() { return new Promise((r0) => { this.ws = new WebSocket(`ws://127.0.0.1:${this.port}/ws/agent`);
    this.ws.onopen = () => { this.ws.send(JSON.stringify({ type: "session:activate", id: this.sid, project: this.project })); setTimeout(r0, 600); };
    this.ws.onmessage = (ev) => { let m; try { m = JSON.parse(ev.data); } catch { return; } if (!this.waiter) return;
      this.waiter.frames.push(m);
      if (m.type === "turn:done") { const w = this.waiter; this.waiter = null; clearTimeout(w.timer); setTimeout(() => w.resolve(w.frames), 400); } }; }); }
  turn(text, capMs = 180000) { return new Promise((resolve) => { const w = { frames: [], resolve, timer: null };
    w.timer = setTimeout(() => { this.waiter = null; resolve(w.frames); }, capMs); this.waiter = w;
    this.ws.send(JSON.stringify({ type: "user", content: text, mode: "efficient" })); }); }
  close() { try { this.ws.close(); } catch {} }
}

const PROJECTS = path.join(os.tmpdir(), "t4a-comp-" + process.pid), STATE = path.join(os.tmpdir(), "t4a-comps-" + process.pid);
let app = null, code = 2;
try {
  await new Promise((r) => tSrv.listen(TGW, "127.0.0.1", r));
  await new Promise((r) => cSrv.listen(CGW, "127.0.0.1", r));
  const d = path.join(PROJECTS, "p", ".tina4-agent", "sessions"); await fs.mkdir(d, { recursive: true });
  await fs.writeFile(path.join(d, "a.json"), JSON.stringify({ id: "a", title: "a", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));
  if (process.env.T4_SEED) {
    // An EXISTING project, so the build lane has something to edit and reaches the coder. Without
    // this the turn stops at "no project yet" and the coder is never called.
    const ws = path.join(PROJECTS, "p");
    await fs.mkdir(path.join(ws, "plan"), { recursive: true });
    await fs.writeFile(path.join(ws, "plan", "MASTER.md"), "# Plan\n\n- [x] 1. scaffold the page\n- [ ] 2. show the time\n");
    await fs.writeFile(path.join(ws, "index.html"), "<!doctype html><html><body><h1>hello</h1></body></html>\n");
  }
  app = spawn("npx", ["tsx", "app.ts"], { cwd: TREE, detached: true,
    env: { ...process.env, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(PORT), TINA4_STATE_DIR: STATE,
      TINA4_MODEL_ENDPOINT: `http://127.0.0.1:${CGW}/v1`, TINA4_MODEL_ID: "fake-coder", TINA4_MODEL_TOKEN: "t",
      TINA4_THINKER_ENDPOINT: `http://127.0.0.1:${TGW}/v1`, TINA4_THINKER_MODEL: "fake-thinker", TINA4_THINKER_TOKEN: "t",
      TINA4_THINKING_MODE: "false", TINA4_THINKER_PLAN: process.env.T4_THINKER_PLAN ?? "1",
      TINA4_PROJECTS_ROOT: PROJECTS, TINA4_CURRENT_PROJECT: "p", TINA4_DEBUG: "false", TINA4_NO_BROWSER: "1" },
    stdio: ["ignore", "ignore", "ignore"] });
  if (!await waitHttp(`http://127.0.0.1:${PORT}/api/model`)) throw new Error("app did not start");

  const s = new Session(PORT, "p", "a"); await s.open();
  const fr = await s.turn(process.env.T4_MSG || "hey, how is this project looking?");
  s.close();
  const done = fr.filter((f) => f.type === "turn:done").pop();
  const sess = JSON.parse(await fs.readFile(path.join(PROJECTS, "p", ".tina4-agent", "sessions", "a.json"), "utf8"));

  const expected = (seen.thinker.json + seen.thinker.sse) * THINKER_TOK + (seen.coder.json + seen.coder.sse) * CODER_TOK;
  console.log("  intent forced      ", INTENT);
  console.log("  thinker calls      ", `json ${seen.thinker.json}  sse ${seen.thinker.sse}   (${THINKER_TOK}/call)`);
  console.log("  coder calls        ", `json ${seen.coder.json}  sse ${seen.coder.sse}   (${CODER_TOK}/call)`);
  console.log("  expected total     ", expected);
  console.log("  turn:done tokens   ", done?.tokens);
  console.log("  session totalTokens", sess.totalTokens);
  const ok = sess.totalTokens === expected && expected > 0;
  console.log("");
  console.log(ok ? "  PASS -- every call the gateways served is in the session total" : "  FAIL -- counter disagrees with what the gateways served");
  if (seen.thinker.sse === 0 && seen.coder.sse === 0) console.log("  NOTE: no STREAMING call happened, so the streaming half is not covered by this run");
  code = ok ? 0 : 1;
} catch (e) { console.error("probe error:", e); code = 2; }
finally {
  try { if (app?.pid) process.kill(-app.pid, "SIGTERM"); } catch {}
  await new Promise((r) => tSrv.close(r)); await new Promise((r) => cSrv.close(r));
  await fs.rm(PROJECTS, { recursive: true, force: true }).catch(() => {});
  await fs.rm(STATE, { recursive: true, force: true }).catch(() => {});
  const left = []; for (const x of [PROJECTS, STATE]) { try { await fs.stat(x); left.push(x); } catch {} }
  console.log(left.length ? "  CLEANUP FAILED: " + left.join(" ") : "  cleanup verified");
}
process.exit(code);
