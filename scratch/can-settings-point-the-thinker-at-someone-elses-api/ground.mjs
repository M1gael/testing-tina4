// w-20, stage 1 — is the absence real, and what already exists that would be duplicated?
//
// The request: add API keys for providers like OpenRouter or DeepSeek in the thinker/coder
// settings. Before designing anything, find out what the shipped tree already does when you try.
//
// Boots the tree under test on an isolated HOME + state dir, then drives the REAL endpoints.
//   usage: T4_TREE=<tree> node ground.mjs
import { mkdtempSync, rmSync, readFileSync, existsSync } from "node:fs";
import { spawn, execFileSync } from "node:child_process";
import os from "node:os"; import path from "node:path";

const TREE = process.env.T4_TREE || "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main";
const PORT = Number(process.env.T4_PORT || 8798);
const HOME = mkdtempSync(path.join(os.tmpdir(), "w20-home-"));
const STATE = path.join(HOME, ".tina4-simple-agent");
const SETTINGS = path.join(STATE, "settings.json");

const boot = () => {
  const p = spawn(path.join(TREE, "node_modules/.bin/tsx"), ["app.ts"], {
    cwd: TREE, detached: true, stdio: ["ignore", "pipe", "pipe"],
    env: { HOME, PATH: process.env.PATH, TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(PORT),
           TINA4_NO_BROWSER: "true", TINA4_PROJECTS_ROOT: path.join(HOME, "projects"),
           TINA4_STATE_DIR: STATE },
  });
  return p;
};
const up = async (ms = 60_000) => {
  const t0 = Date.now();
  for (;;) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/api/model`); if (r.ok) return true; } catch {}
    if (Date.now() - t0 > ms) return false;
    await new Promise((r) => setTimeout(r, 500));
  }
};
const kill = (p) => { try { process.kill(-p.pid, "SIGTERM"); } catch {} };
const get = () => fetch(`http://127.0.0.1:${PORT}/api/model`).then((r) => r.json());
const post = (body) => fetch(`http://127.0.0.1:${PORT}/api/model`, {
  method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }).then((r) => r.status);

const OPENROUTER = { endpoint: "https://openrouter.ai/api/v1", model: "deepseek/deepseek-chat", token: "sk-or-v1-GROUNDPROBE" };

let srv = boot();
if (!await up()) { console.log("server never came up"); kill(srv); rmSync(HOME, { recursive: true, force: true }); process.exit(2); }

console.log(`tree   ${TREE}`);
console.log(`stamp  ${execFileSync("git", ["-C", TREE, "describe", "--tags", "--always"], { encoding: "utf8" }).trim()}`);

const before = await get();
console.log(`\n--- as shipped ---`);
console.log(`  coder endpoint      ${before.endpoint}`);
console.log(`  coder model         ${before.model}`);
console.log(`  thinker endpoint    ${before.thinker?.endpoint}`);
console.log(`  thinker model       ${before.thinker?.model}`);
console.log(`  coderVendor         ${before.coderVendor}`);
console.log(`  thinkerVendor       ${before.thinkerVendor}`);
console.log(`  vendors offered     ${(before.vendors || []).map((v) => `${v.id}(${v.adapter})`).join(", ")}`);

console.log(`\n--- POST a third-party THINKER (what the request asks for) ---`);
const s1 = await post({ thinkerEndpoint: OPENROUTER.endpoint, thinkerModel: OPENROUTER.model, thinkerToken: OPENROUTER.token });
const afterT = await get();
console.log(`  POST status         ${s1}`);
console.log(`  thinker endpoint    ${afterT.thinker?.endpoint}   ${afterT.thinker?.endpoint === OPENROUTER.endpoint ? "STUCK" : "REVERTED"}`);
console.log(`  thinker model       ${afterT.thinker?.model}   ${afterT.thinker?.model === OPENROUTER.model ? "STUCK" : "REVERTED"}`);

console.log(`\n--- POST a third-party CODER ---`);
const s2 = await post({ endpoint: OPENROUTER.endpoint, model: OPENROUTER.model, token: OPENROUTER.token });
const afterC = await get();
console.log(`  POST status         ${s2}`);
console.log(`  coder endpoint      ${afterC.endpoint}   ${afterC.endpoint === OPENROUTER.endpoint ? "STUCK" : "REVERTED"}`);
console.log(`  coder model         ${afterC.model}   ${afterC.model === OPENROUTER.model ? "STUCK" : "REVERTED"}`);

console.log(`\n--- what landed on disk ---`);
const disk = existsSync(SETTINGS) ? JSON.parse(readFileSync(SETTINGS, "utf8")) : null;
if (!disk) console.log("  settings.json was never written");
else {
  console.log(`  settings.json       ${SETTINGS}`);
  console.log(`  token               ${JSON.stringify(disk.token)}`);
  console.log(`  thinkerToken        ${JSON.stringify(disk.thinkerToken)}`);
  console.log(`  key in PLAINTEXT    ${JSON.stringify(readFileSync(SETTINGS, "utf8")).includes("GROUNDPROBE")}`);
  try { console.log(`  file mode           ${(execFileSync("stat", ["-c", "%a", SETTINGS], { encoding: "utf8" })).trim()}`); } catch {}
}

console.log(`\n--- survives a restart? ---`);
kill(srv); await new Promise((r) => setTimeout(r, 1500));
srv = boot();
if (!await up()) console.log("  restart failed");
else {
  const re = await get();
  console.log(`  thinker endpoint    ${re.thinker?.endpoint}`);
  console.log(`  coder endpoint      ${re.endpoint}`);
}

console.log(`\n--- what the Settings UI offers (source count, not a browser) ---`);
const ui = readFileSync(path.join(TREE, "public/app.js"), "utf8");
for (const [what, re] of [
  ["raw coder endpoint field", /Model endpoint/],
  ["raw coder model field", /Model id/],
  ["raw coder bearer field", /Bearer token/],
  ["ANY thinker endpoint field", /[Tt]hinker endpoint/],
  ["ANY thinker token field", /[Tt]hinker (token|key)/],
  ["the in-memory claim", /Stored in-memory server-side only/],
]) console.log(`  ${what.padEnd(26)} ${re.test(ui)}`);

kill(srv); await new Promise((r) => setTimeout(r, 1000));
rmSync(HOME, { recursive: true, force: true });
console.log(`\nhome removed: ${!existsSync(HOME)}`);
