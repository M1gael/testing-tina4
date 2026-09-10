// Does the localStorage write actually cost the splitter drag anything?
//
// ui-01 / w-15 has been reported twice by the operator and profiled zero times. The mechanism
// read from source is: public/app.js:1752 persists previewWidth on every signal write, and the
// move closure at :1795 assigns on every mousemove sample with no rAF coalescing. That is a
// theory. This measures it.
//
// The causal test is the A/B, not the absolute numbers:
//   A  the page as it ships
//   B  identical, with Storage.prototype.setItem stubbed to a no-op
// The signal write, the effect and the DOM update all still happen in B. ONLY the disk write is
// removed. If B is not materially faster than A, the localStorage write is not the cost and the
// proposed fix is a guess that happens to be plausible.
//
//   node probe.mjs [movesPerDrag] [repeats]
//
// Reports per run: wall time for the move burst, moves delivered, setItem calls and their
// cumulative self-time, and long-task total.
//
// NOTE ON WHAT THIS IS: moves are dispatched back-to-back, faster than a 60-125Hz mouse. That is
// deliberate — it is the flood condition that makes a drag feel laggy — but it means the numbers
// are throughput under load, not latency under real input. Headless, on this machine.

import { createRequire } from "node:module";

// puppeteer-core is the harness's dependency, not ours — resolve it from there rather than
// installing a second copy next to a throwaway script.
const HARNESS = "/var/home/work/gitdir/tina4-simple-agent-work/baseline-main/";
const puppeteer = createRequire(HARNESS + "package.json")("puppeteer-core");

const HOST = "http://127.0.0.1:8790";
const CHROME = "/usr/bin/chromium-browser";
const MOVES = Number(process.argv[2] || 200);
const REPEATS = Number(process.argv[3] || 3);
const PROJECT = "t4a-probe-splitter";

const api = async (p, init) => {
  const r = await fetch(HOST + p, { headers: { "content-type": "application/json" }, ...init });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`${p} -> HTTP ${r.status} ${JSON.stringify(j).slice(0, 200)}`);
  return j;
};

// The welcome modal is not closable on first run (`closable = !isFirstRun.value`,
// public/app.js:2883), and it covers the toolbar. A project is the way past it.
console.log(`creating throwaway project ${PROJECT} (deleted at the end)`);
await api("/api/projects", { method: "POST", body: JSON.stringify({ name: PROJECT }) });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,1000"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000 });
await page.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });

// previewVisible is
//   computed(() => (previewNonce.value > 0 || !!service.value) && !previewClosed.value)
// and on this tree it comes up true already, so the splitter is usually present on load. Click
// the eye only if it is not.
await new Promise((r) => setTimeout(r, 1200));
if (!(await page.$(".preview-splitter"))) {
  await page.click('button[title="Show preview"]');
  await page.waitForSelector(".preview-splitter", { timeout: 10_000 });
  console.log("preview toggled on");
}
await page.waitForSelector(".preview-splitter", { timeout: 10_000 });
console.log("splitter present\n");

const INSTRUMENT = () => {
  const w = window;
  w.__probe = { moves: 0, setItemCalls: 0, setItemMs: 0, longtasks: 0, longtaskMs: 0 };
  if (!w.__origSetItem) w.__origSetItem = Storage.prototype.setItem;
  Storage.prototype.setItem = function (...a) {
    const t = performance.now();
    const r = w.__origSetItem.apply(this, a);
    w.__probe.setItemMs += performance.now() - t;
    w.__probe.setItemCalls++;
    return r;
  };
  if (!w.__moveCounter) {
    w.__moveCounter = () => w.__probe.moves++;
    document.addEventListener("mousemove", w.__moveCounter, true);
  }
  if (!w.__lto) {
    w.__lto = new PerformanceObserver((l) => {
      for (const e of l.getEntries()) { w.__probe.longtasks++; w.__probe.longtaskMs += e.duration; }
    });
    try { w.__lto.observe({ entryTypes: ["longtask"] }); } catch {}
  }
};

// B: the signal write, the effect and the DOM update all still run. Only the disk write goes.
const STUB_STORAGE = () => {
  const w = window;
  Storage.prototype.setItem = function (...a) { w.__probe.setItemCalls++; return undefined; };
};

const RESET = () => { const p = window.__probe; p.moves = 0; p.setItemCalls = 0; p.setItemMs = 0; p.longtasks = 0; p.longtaskMs = 0; };
const READ = () => ({ ...window.__probe, width: Number(localStorage.getItem("t4a.previewWidth")) || null });

async function drag(moves) {
  const box = await page.$eval(".preview-splitter", (el) => {
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  });
  await page.mouse.move(box.x, box.y);
  await page.mouse.down();
  const t0 = Date.now();
  // Sweep left then back, staying inside the clamp (280 .. innerWidth-320).
  for (let i = 0; i < moves; i++) {
    const dx = Math.round(120 * Math.sin((i / moves) * Math.PI * 2));
    await page.mouse.move(box.x + dx, box.y);
  }
  const ms = Date.now() - t0;
  await page.mouse.up();
  return ms;
}

const rows = [];
for (const variant of ["A: as it ships", "B: setItem stubbed"]) {
  await page.evaluate(INSTRUMENT);
  if (variant.startsWith("B")) await page.evaluate(STUB_STORAGE);
  for (let r = 0; r < REPEATS; r++) {
    await page.evaluate(RESET);
    const ms = await drag(MOVES);
    const p = await page.evaluate(READ);
    rows.push({ variant, run: r + 1, ms, ...p });
    console.log(
      `${variant.padEnd(20)} run ${r + 1}  ${String(ms).padStart(5)}ms for ${MOVES} moves` +
      `  · delivered ${String(p.moves).padStart(4)}` +
      `  · setItem ${String(p.setItemCalls).padStart(4)} calls / ${p.setItemMs.toFixed(1)}ms` +
      `  · longtasks ${p.longtasks} / ${p.longtaskMs.toFixed(0)}ms`
    );
  }
  console.log("");
}

const mean = (v, k) => v.reduce((a, b) => a + b[k], 0) / v.length;
const A = rows.filter((r) => r.variant.startsWith("A"));
const B = rows.filter((r) => r.variant.startsWith("B"));
console.log("=== means ===");
console.log(`A as it ships       ${mean(A, "ms").toFixed(0)}ms   setItem self-time ${mean(A, "setItemMs").toFixed(1)}ms   longtask ${mean(A, "longtaskMs").toFixed(0)}ms`);
console.log(`B setItem stubbed   ${mean(B, "ms").toFixed(0)}ms   setItem self-time ${mean(B, "setItemMs").toFixed(1)}ms   longtask ${mean(B, "longtaskMs").toFixed(0)}ms`);
const delta = mean(A, "ms") - mean(B, "ms");
console.log(`\ndelta ${delta.toFixed(0)}ms (${((delta / mean(A, "ms")) * 100).toFixed(1)}% of A) — this is the localStorage write's share.`);
console.log(`per move: A ${(mean(A, "ms") / MOVES).toFixed(2)}ms · B ${(mean(B, "ms") / MOVES).toFixed(2)}ms`);

await page.evaluate(() => { if (window.__origSetItem) Storage.prototype.setItem = window.__origSetItem; });
await browser.close();

console.log(`\ndeleting throwaway project ${PROJECT}`);
await api("/api/projects", { method: "POST", body: JSON.stringify({ action: "delete", name: PROJECT }) })
  .catch((e) => console.log(`  could not delete via API (${e.message}) — remove ~/tina4-projects/${PROJECT} by hand`));
