// The w-20 gate proves a REAL TURN reaches a custom provider. It proves it for the THINKER.
//
// In gate.mjs both roles point at the SAME fake, so a chat arriving there could be either role. In
// attack.mjs the roles point at different fakes, but the turn used ("what does this project do?")
// is a question -- answered by the thinker alone, and the coder's provider saw 0 chats. So
// "the coder's chat goes to the coder's provider with the coder's key" was INFERRED from
// `adapter !== "cli"` routing, never observed.
//
// This observes it, or says it could not.
//
//   T4_TREE=<tree> node does-the-coder-really-call-it.mjs
import http from "node:http";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const APP_PORT = Number(process.env.T4_PORT || 8771);
const A_PORT = Number(process.env.T4_A_PORT || 8961);   // coder
const B_PORT = Number(process.env.T4_B_PORT || 8962);   // thinker
const KEY_A = "sk-CODERSIDE-aaaa", KEY_B = "sk-THINKERSIDE-bbbb";
const MODEL_A = "coder-model", MODEL_B = "thinker-model";
const HOME = path.join(os.tmpdir(), "w20-coder-" + process.pid);

const seen = { A: [], B: [] };
const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
function provider(which, model) {
  return http.createServer((req, res) => {
    if (req.method === "GET") {
      seen[which].push({ kind: "models", auth: req.headers.authorization || "" });
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ data: [{ id: model, context_window: 64000 }] })); return;
    }
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      let b = null; try { b = JSON.parse(body); } catch {}
      const sys = String(b?.messages?.[0]?.content ?? "");
      seen[which].push({ kind: "chat", auth: req.headers.authorization || "", model: b?.model, sys: sys.slice(0, 60) });
      const maxTok = Number(b?.max_tokens ?? 0);
      // Answer like a coder when asked to write a file, so the pipeline keeps going rather than
      // bailing out and never reaching the coder at all.
      const answer = maxTok > 0 && maxTok <= 8 ? "BUILD"
        : /\bJSON\b/i.test(sys) ? '{"action":"build","files":[{"path":"hello.txt","why":"asked for"}],"acceptance":"file exists","locate":""}'
        : "```hello.txt\nhi\n```";
      if (b && b.stream === false) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }],
          usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } })); return;
      }
      res.writeHead(200, { "content-type": "text/event-stream" });
      sse(res, { choices: [{ delta: { role: "assistant" } }] });
      sse(res, { choices: [{ delta: { content: answer } }] });
      sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
      res.write("data: [DONE]\n\n"); res.end();
    });
  });
}
const A = provider("A", MODEL_A), B = provider("B", MODEL_B);
const EP_A = `http://127.0.0.1:${A_PORT}/v1`, EP_B = `http://127.0.0.1:${B_PORT}/v1`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

await new Promise((r) => A.listen(A_PORT, "127.0.0.1", r));
await new Promise((r) => B.listen(B_PORT, "127.0.0.1", r));
await fs.mkdir(path.join(HOME, "projects", "p", ".tina4-agent", "sessions"), { recursive: true });
await fs.writeFile(path.join(HOME, "projects", "p", ".tina4-agent", "sessions", "c.json"),
  JSON.stringify({ id: "c", title: "coder", status: "active", createdAt: 1, updatedAt: 1, messages: [] }));

const app = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
  cwd: TREE, detached: true, stdio: ["ignore", "ignore", "pipe"],
  env: { HOME, PATH: process.env.PATH, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(APP_PORT),
         TINA4_NO_BROWSER: "1", TINA4_PROJECTS_ROOT: path.join(HOME, "projects"),
         TINA4_CURRENT_PROJECT: "p", TINA4_STATE_DIR: path.join(HOME, ".tina4-simple-agent"), TINA4_THINKER_PLAN: "0" },
});
app.stderr.on("data", () => {});
let up = false;
for (let i = 0; i < 120 && !up; i++) { try { up = (await fetch(`http://127.0.0.1:${APP_PORT}/api/model`)).ok; } catch {} if (!up) await sleep(500); }

let selected = null;
const frames = [];
if (up) {
  const post = (b) => fetch(`http://127.0.0.1:${APP_PORT}/api/model`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(b) });
  await post({ coderVendor: "custom", endpoint: EP_A, model: MODEL_A, token: KEY_A });
  await post({ thinkerVendor: "custom", thinkerEndpoint: EP_B, thinkerModel: MODEL_B, thinkerToken: KEY_B });
  // Autopilot on: without it the build stops for an approval nobody is here to give, and "the coder
  // never ran" would mean "the probe never let it", which answers nothing.
  await post({ autoPilot: true });
  selected = await fetch(`http://127.0.0.1:${APP_PORT}/api/model`).then((r) => r.json());
  seen.A.length = 0; seen.B.length = 0;
  // A turn that has to write code. Capped -- a suite for "the coder runs" must not hang waiting.
  await new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${APP_PORT}/ws/agent`);
    const done = setTimeout(resolve, 150_000);
    ws.onopen = () => { ws.send(JSON.stringify({ type: "session:activate", id: "c", project: "p" }));
      setTimeout(() => ws.send(JSON.stringify({ type: "user", content: "create a file hello.txt containing the word hi", mode: "quick" })), 600); };
    ws.onmessage = (ev) => { let m; try { m = JSON.parse(ev.data); } catch { return; }
      frames.push(m.type + (m.type === "activity" || m.type === "mech" ? ` (${String(m.text || "").slice(0, 70)})` : ""));
      if (m.type === "turn:done") { clearTimeout(done); setTimeout(resolve, 500); } };
  });
}
try { process.kill(-app.pid, "SIGTERM"); } catch {}
await sleep(600); A.close(); B.close();
await fs.rm(HOME, { recursive: true, force: true }).catch(() => {});

console.log(`  tree                ${TREE}`);
console.log(`  app came up         ${up}`);
console.log(`  coder selected as   ${selected?.coderVendor} ${selected?.endpoint}`);
console.log(`  thinker selected as ${selected?.thinkerVendor} ${selected?.thinker?.endpoint}`);
// What the turn actually did. "The coder never ran" is only interesting once you can see whether
// the turn ever asked for code in the first place.
console.log(`  frames              ${frames.length}`);
for (const f of [...new Set(frames)].slice(0, 24)) console.log(`     ${f}`);
for (const w of ["A", "B"]) {
  const chats = seen[w].filter((x) => x.kind === "chat");
  console.log(`  provider ${w} (${w === "A" ? "coder " : "thinker"})  ${seen[w].length} request(s), ${chats.length} chat  auth: ${[...new Set(seen[w].map((x) => x.auth))].join(" | ") || "none"}`);
}
const aChats = seen.A.filter((x) => x.kind === "chat");
const aAllOwnKey = seen.A.length > 0 && seen.A.every((x) => x.auth === `Bearer ${KEY_A}`);
console.log();
if (!up) { console.log("  UNPROVEN — the app never started"); process.exit(2); }
if (!aChats.length) { console.log("  UNPROVEN — no CHAT reached the coder's provider; this turn never ran the coder"); process.exit(2); }
console.log(aAllOwnKey
  ? `  OBSERVED — the coder's chat reached the coder's provider under the coder's key (${aChats.length} chat call(s))`
  : `  WRONG — the coder's provider saw a key that is not the coder's`);
process.exit(aAllOwnKey ? 0 : 1);
