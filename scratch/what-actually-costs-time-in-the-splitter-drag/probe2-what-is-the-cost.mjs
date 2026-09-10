// Round 1 (probe.mjs) killed the theory: stubbing localStorage.setItem changed a 200-move drag
// by -2ms out of 3326ms. But every run took 3324-3329ms — 16.6ms per move, dead constant, ~60Hz.
// That is a frame-paced CDP dispatch floor, not the page's handler cost. So round 1 could prove
// what is NOT the cost and could not see what IS.
//
// This adds the control that separates them:
//
//   CONTROL   the same move burst with NO mousedown — the drag handler is never installed, so
//             this is pure dispatch overhead
//   DRAG      identical burst with the button held
//
// handler cost = DRAG - CONTROL. If they match, the app is doing nothing measurable per move and
// the lag is somewhere this harness cannot reach — which is itself the finding.
//
// Also reads Chromium's own Performance domain, which attributes time to script vs style vs
// layout rather than guessing from wall clock.
//
//   node probe2-what-is-the-cost.mjs [moves] [repeats]

import { createRequire } from "node:module";
const HARNESS = "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main/";
const puppeteer = createRequire(HARNESS + "package.json")("puppeteer-core");

const HOST = "http://127.0.0.1:8790";
const MOVES = Number(process.argv[2] || 200);
const REPEATS = Number(process.argv[3] || 3);
const PROJECT = "t4a-probe-splitter";

const api = async (p, init) => {
  const r = await fetch(HOST + p, { headers: { "content-type": "application/json" }, ...init });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`${p} -> HTTP ${r.status} ${JSON.stringify(j).slice(0, 200)}`);
  return j;
};

await api("/api/projects", { method: "POST", body: JSON.stringify({ name: PROJECT }) }).catch(() => {});

const browser = await puppeteer.launch({
  executablePath: "/usr/bin/chromium-browser",
  headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,1000"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000 });
await page.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise((r) => setTimeout(r, 1200));
if (!(await page.$(".preview-splitter"))) await page.click('button[title="Show preview"]');
await page.waitForSelector(".preview-splitter", { timeout: 10_000 });

const cdp = await page.target().createCDPSession();
await cdp.send("Performance.enable");
const metrics = async () => Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
const sub = (a, b) => ({
  script: (a.ScriptDuration - b.ScriptDuration) * 1000,
  style: (a.RecalcStyleDuration - b.RecalcStyleDuration) * 1000,
  layout: (a.LayoutDuration - b.LayoutDuration) * 1000,
  task: (a.TaskDuration - b.TaskDuration) * 1000,
  layouts: a.LayoutCount - b.LayoutCount,
  styles: a.RecalcStyleCount - b.RecalcStyleCount,
});

// The splitter MOVES once a drag resizes the pane. Caching its box across runs made every drag
// after the first miss it entirely — `delivered 0`, and three runs that looked like data.
// Re-read it before every burst.
const splitterBox = () => page.$eval(".preview-splitter", (el) => {
  const r = el.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
});

await page.evaluate(() => {
  window.__moves = 0;
  document.addEventListener("mousemove", () => window.__moves++, true);
});

async function burst(held) {
  const box = await splitterBox();
  await page.mouse.move(box.x, box.y);
  if (held) await page.mouse.down();
  await page.evaluate(() => (window.__moves = 0));
  const before = await metrics();
  const t0 = Date.now();
  for (let i = 0; i < MOVES; i++) {
    const dx = Math.round(120 * Math.sin((i / MOVES) * Math.PI * 2));
    await page.mouse.move(box.x + dx, box.y);
  }
  const ms = Date.now() - t0;
  const after = await metrics();
  if (held) await page.mouse.up();
  const delivered = await page.evaluate(() => window.__moves);
  return { ms, delivered, ...sub(after, before) };
}

const out = { CONTROL: [], DRAG: [] };
for (let r = 0; r < REPEATS; r++) {
  for (const [name, held] of [["CONTROL", false], ["DRAG", true]]) {
    const v = await burst(held);
    out[name].push(v);
    console.log(
      `${name.padEnd(8)} run ${r + 1}  wall ${String(v.ms).padStart(5)}ms  delivered ${String(v.delivered).padStart(4)}` +
      `  · script ${v.script.toFixed(1).padStart(7)}ms  style ${v.style.toFixed(1).padStart(6)}ms  layout ${v.layout.toFixed(1).padStart(6)}ms` +
      `  · layouts ${String(v.layouts).padStart(4)}  styleRecalcs ${String(v.styles).padStart(4)}`
    );
  }
}

const mean = (a, k) => a.reduce((s, x) => s + x[k], 0) / a.length;
console.log("\n=== means over", REPEATS, "runs,", MOVES, "moves each ===");
for (const k of ["ms", "delivered", "script", "style", "layout", "layouts", "styles"]) {
  const c = mean(out.CONTROL, k), d = mean(out.DRAG, k);
  console.log(`  ${k.padEnd(10)} control ${c.toFixed(1).padStart(8)}   drag ${d.toFixed(1).padStart(8)}   delta ${(d - c).toFixed(1).padStart(8)}`);
}
const handler = mean(out.DRAG, "script") - mean(out.CONTROL, "script");
console.log(`\nscript time attributable to the drag handler: ${handler.toFixed(1)}ms over ${MOVES} moves = ${(handler / MOVES).toFixed(3)}ms per move`);
console.log(`wall-clock floor imposed by this harness: ${(mean(out.CONTROL, "ms") / MOVES).toFixed(2)}ms per dispatched move (CDP round-trip, frame-paced)`);

await browser.close();
await api("/api/projects", { method: "POST", body: JSON.stringify({ action: "delete", name: PROJECT }) }).catch(() => {});
