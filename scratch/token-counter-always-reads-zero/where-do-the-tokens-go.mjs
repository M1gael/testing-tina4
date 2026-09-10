// run-20 -- stage 3. WHERE do the tokens go? Not read from the source: measured.
//
// Two SEPARATE fake gateways so thinker and coder calls cannot be confused: the thinker gateway
// reports 1000 tokens per call, the coder gateway 7. Then look at every place the app could put a
// token count and see which numbers arrived.
//
//   T4TREE=.../baseline-main node where-do-the-tokens-go.mjs
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE = process.env.T4TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const THINKER_PORT = 8901, CODER_PORT = 8902, APP_PORT = 8792;
const PROJECTS = path.join(os.tmpdir(), "t4a-run20b-" + process.pid);
const STATE = path.join(os.tmpdir(), "t4a-run20b-state-" + process.pid);

const log = { thinker: [], coder: [] };
function gateway(role, tokens) {
  const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
  return http.createServer((req, res) => {
    if (req.method !== "POST") { res.writeHead(404).end(); return; }
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      let b0 = null; try { b0 = JSON.parse(body); } catch {}
      const maxTok = Number(b0?.max_tokens ?? 0);
      const sys = String(b0?.messages?.[0]?.content ?? "");
      // The app probes intent with max_tokens<=8 and expects one word. Anything else (or an empty
      // 200) is read as an offline stub and the turn opens Setup instead of running -- which is how
      // the first draft of this probe measured a turn that had already given up.
      const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
        : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
        : "It is a small static page. Nothing is broken.";
      const streaming = !(b0 && b0.stream === false);
      log[role].push({ streaming, tokens });
      const usage = { prompt_tokens: Math.floor(tokens * 0.8), completion_tokens: Math.ceil(tokens * 0.2), total_tokens: tokens };
      if (!streaming) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }], usage }));
        return;
      }
      res.writeHead(200, { "content-type": "text/event-stream" });
      sse(res, { choices: [{ delta: { role: "assistant" } }] });
      sse(res, { choices: [{ delta: { content: answer } }] });
      sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
      sse(res, { choices: [], usage });          // usage in the final frame, exactly as the real gateway sends it
      res.write("data: [DONE]\n\n"); res.end();
    });
  });
}
const thinkerSrv = gateway("thinker", 1000), coderSrv = gateway("coder", 7);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitHttp(url, tries = 60) { for (let i = 0; i < tries; i++) { try { const r = await fetch(url); if (r.ok) return true; } catch {} await sleep(250); } return false; }
function runTurn(project, sid, userMsg, capMs = 90000) {
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${APP_PORT}/ws/agent`); const frames = [];
    const t = setTimeout(() => { try { ws.close(); } catch {} resolve({ frames, timedOut: true }); }, capMs);
    ws.onopen = () => { ws.send(JSON.stringify({ type: "session:activate", id: sid, project }));
      setTimeout(() => ws.send(JSON.stringify({ type: "user", content: userMsg, mode: "efficient" })), 400); };
    ws.onmessage = (ev) => { let m; try { m = JSON.parse(ev.data); } catch { return; } frames.push(m);
      if (m.type === "turn:done") { clearTimeout(t); setTimeout(() => { try { ws.close(); } catch {} resolve({ frames, timedOut: false }); }, 400); } };
  });
}

let app = null;
async function main() {
  await new Promise((r) => thinkerSrv.listen(THINKER_PORT, "127.0.0.1", r));
  await new Promise((r) => coderSrv.listen(CODER_PORT, "127.0.0.1", r));
  const dir = path.join(PROJECTS, "p", ".tina4-agent", "sessions");
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, "s1.json"), JSON.stringify({ id: "s1", title: "run20", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));

  app = spawn("npx", ["tsx", "app.ts"], { cwd: TREE, detached: true,
    env: { ...process.env, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(APP_PORT), TINA4_STATE_DIR: STATE,
      TINA4_MODEL_ENDPOINT: `http://127.0.0.1:${CODER_PORT}/v1`, TINA4_MODEL_ID: "fake-coder", TINA4_MODEL_TOKEN: "t",
      TINA4_THINKER_ENDPOINT: `http://127.0.0.1:${THINKER_PORT}/v1`, TINA4_THINKER_MODEL: "fake-thinker", TINA4_THINKER_TOKEN: "t",
      TINA4_THINKING_MODE: "false", TINA4_THINKER_PLAN: process.env.T4_THINKER_PLAN ?? "0",
      TINA4_PROJECTS_ROOT: PROJECTS, TINA4_CURRENT_PROJECT: "p", TINA4_DEBUG: "false", TINA4_NO_BROWSER: "1" },
    stdio: ["ignore", "ignore", "pipe"] });
  let stderr = ""; app.stderr.on("data", (c) => { stderr += c; });
  if (!await waitHttp(`http://127.0.0.1:${APP_PORT}/api/model`)) { console.error("app did not start\n", stderr.slice(-1500)); return 2; }

  const { frames, timedOut } = await runTurn("p", "s1", process.env.T4_MSG || "say hi");
  const done = frames.filter((f) => f.type === "turn:done").pop();
  const costFrames = frames.filter((f) => f.type === "cost");

  const ws0 = path.join(PROJECTS, "p");
  const costDir = path.join(ws0, "plan", "cost");
  const costFiles = await fs.readdir(costDir).catch(() => []);
  let ledger = [];
  for (const f of costFiles) {
    const txt = await fs.readFile(path.join(costDir, f), "utf8").catch(() => "");
    for (const l of txt.split("\n")) if (l.trim()) { try { ledger.push(JSON.parse(l)); } catch {} }
  }
  const sess = JSON.parse(await fs.readFile(path.join(ws0, ".tina4-agent", "sessions", "s1.json"), "utf8").catch(() => "{}"));
  const api = await fetch(`http://127.0.0.1:${APP_PORT}/api/model`).then((r) => r.json()).catch(() => ({}));

  const sum = (a) => a.reduce((n, x) => n + x.tokens, 0);
  console.log("  tree                    ", TREE, "  timedOut:", timedOut);
  console.log("  message                 ", JSON.stringify(process.env.T4_MSG || "say hi"), " THINKER_PLAN=", process.env.T4_THINKER_PLAN ?? "0");
  console.log("");
  console.log("  gateway calls made      thinker", log.thinker.length, "calls =", sum(log.thinker), "tokens  |  coder", log.coder.length, "calls =", sum(log.coder), "tokens");
  console.log("  ...of which streaming   thinker", log.thinker.filter(x=>x.streaming).length, " coder", log.coder.filter(x=>x.streaming).length);
  console.log("");
  console.log("  turn:done frame         tokens:", done?.tokens, " totalTokens:", done?.totalTokens, " totalElapsedMs:", done?.totalElapsedMs);
  console.log("  persisted session       totalTokens:", sess.totalTokens, " totalElapsedMs:", sess.totalElapsedMs);
  console.log("  cost frames sent        ", costFrames.length);
  console.log("  plan/cost/*.jsonl rows  ", ledger.length, ledger.length ? JSON.stringify(ledger.map(r => ({ role: r.role, vendor: r.vendor, in: r.tokensIn, out: r.tokensOut }))) : "(none)");
  console.log("  COST.md                 ", await fs.stat(path.join(ws0, "COST.md")).then(() => "written").catch(() => "(absent)"));
  console.log("  GET /api/model .cost    ", JSON.stringify(api.cost ?? api.projectCost ?? null));
  console.log("");
  const thinkerLanded = ledger.some((r) => r.role === "thinker");
  console.log("  thinker tokens recorded anywhere? ", thinkerLanded ? "YES" : "NO");
  console.log("  session counter moved?            ", Number(sess.totalTokens) > 0 ? "YES" : "NO");
  return 0;
}

let code = 2;
try { code = await main(); } catch (e) { console.error("probe error:", e); }
finally {
  try { if (app && app.pid) process.kill(-app.pid, "SIGTERM"); } catch {}
  await new Promise((r) => thinkerSrv.close(r)); await new Promise((r) => coderSrv.close(r));
  await fs.rm(PROJECTS, { recursive: true, force: true }).catch(() => {});
  await fs.rm(STATE, { recursive: true, force: true }).catch(() => {});
  const left = []; for (const d of [PROJECTS, STATE]) { try { await fs.stat(d); left.push(d); } catch {} }
  console.log(left.length ? "  CLEANUP FAILED: " + left.join(" ") : "  cleanup verified: throwaway dirs gone");
}
process.exit(code);
