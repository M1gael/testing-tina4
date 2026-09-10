// w-15 / ui-01 — how sluggish is the splitter drag, and where does the time go?
//
// Drives a REAL drag through CDP input (Input.dispatchMouseEvent via page.mouse), not synthetic
// JS events, so the production path runs: mousedown handler -> document mousemove -> signal write
// -> localStorage effect -> style binding -> recalc + layout of the whole grid incl. the iframe.
//
// Reports, per drag of N samples:
//   setItem      localStorage writes, and total ms spent inside them
//   frames       animation frames actually painted during the drag
//   recalc/layout Chrome's own accounting (Performance.getMetrics deltas)
//   settle       ms after the last mousemove until the rendered width stops changing
//   tracking     rendered width vs commanded width at each sample — the visible lag
//
//   T4A=http://127.0.0.1:8795 node drag.mjs [label]

import { createRequire } from "node:module";
import { writeFileSync, mkdirSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
mkdirSync("out", { recursive: true });

const HOST  = process.env.T4A || "http://127.0.0.1:8795";
const LABEL = process.argv[2] || "run";
const SAMPLES = Number(process.env.SAMPLES || 60);
const STEP    = Number(process.env.STEP || 4);      // px per sample
const GAP     = Number(process.env.GAP || 8);       // ms between samples (~125Hz, a real mouse)

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));

const cdp = await p.target().createCDPSession();
await cdp.send("Performance.enable");
// A dev box is not the machine the operator is on, and a drag competes with whatever else the
// page is doing. Throttling is how the second user gets visited.
const CPU = Number(process.env.CPU || 1);
if (CPU > 1) await cdp.send("Emulation.setCPUThrottlingRate", { rate: CPU });
const metrics = async () => Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map(m => [m.name, m.value]));

// Instrument the page: count localStorage writes and time inside them, and sample painted frames.
await p.evaluate(() => {
  const proto = Object.getPrototypeOf(localStorage);
  const real = proto.setItem;
  window.__ls = { calls: 0, ms: 0, keys: {} };
  proto.setItem = function (k, v) {
    const t0 = performance.now();
    const r = real.call(this, k, v);
    window.__ls.ms += performance.now() - t0;
    window.__ls.calls++; window.__ls.keys[k] = (window.__ls.keys[k] || 0) + 1;
    return r;
  };
  window.__frames = [];
  window.__rafOn = true;
  // Count frames ONLY. An earlier version read getComputedStyle(...) here every frame, which
  // itself forces a style recalculation -- it inflated RecalcStyleCount and RecalcStyleDuration
  // and was measuring the probe, not the app.
  const tick = () => {
    if (!window.__rafOn) return;
    window.__frames.push(performance.now());
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
});

// The custom element is display:contents — its own box is 0x0 at 0,0. The draggable thing is
// the inner div it renders. Aiming at the host silently clicked the topbar and measured nothing.
const box = await p.$eval(".preview-splitter", el => { const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; });
if (!(box.x > 0 && box.y > 0)) { console.error("splitter has no box -- refusing to measure"); await b.close(); process.exit(2); }
const startW = await p.evaluate(() => parseFloat(getComputedStyle(document.querySelector(".main")).getPropertyValue("--preview-w")));

const m0 = await metrics();
await p.evaluate(() => { window.__ls.calls = 0; window.__ls.ms = 0; window.__ls.keys = {}; window.__frames.length = 0; window.__t0 = performance.now(); });

await p.mouse.move(box.x, box.y);
await p.mouse.down();
const commanded = [];
const wall0 = Date.now();
for (let i = 1; i <= SAMPLES; i++) {
  await p.mouse.move(box.x - i * STEP, box.y);          // drag left = widen the preview
  commanded.push(startW + i * STEP);
  await new Promise(r => setTimeout(r, GAP));
}
const dragMs = Date.now() - wall0;
await p.mouse.up();

// How long after the last input until the rendered width stops moving?
const settle = await p.evaluate(async () => {
  const el = document.querySelector(".main");
  const read = () => parseFloat(getComputedStyle(el).getPropertyValue("--preview-w"));
  const t0 = performance.now(); let last = read(), stableSince = t0;
  for (;;) {
    await new Promise(r => requestAnimationFrame(r));
    const now = performance.now(), v = read();
    if (v !== last) { last = v; stableSince = now; }
    if (now - stableSince > 200) return { settleMs: Math.round(stableSince - t0), finalW: v };
    if (now - t0 > 3000) return { settleMs: -1, finalW: v };
  }
});

const m1 = await metrics();
const page = await p.evaluate(() => { window.__rafOn = false; return { ls: window.__ls, frames: window.__frames.length, span: window.__frames.length ? window.__frames.at(-1) - window.__frames[0] : 0 }; });

const d = (k) => +((m1[k] ?? 0) - (m0[k] ?? 0)).toFixed(4);
const out = {
  label: LABEL, host: HOST, cpuThrottle: Number(process.env.CPU || 1), samples: SAMPLES, stepPx: STEP, gapMs: GAP,
  dragWallMs: dragMs,
  intendedMs: SAMPLES * GAP,
  overrunPct: +(((dragMs / (SAMPLES * GAP)) - 1) * 100).toFixed(1),
  framesPainted: page.frames,
  framesPerSample: +(page.frames / SAMPLES).toFixed(2),
  fpsDuringDrag: page.span > 0 ? +((page.frames / page.span) * 1000).toFixed(1) : null,
  localStorageWrites: page.ls.calls,
  localStorageMs: +page.ls.ms.toFixed(1),
  localStorageKeys: page.ls.keys,
  recalcStyleMs: +(d("RecalcStyleDuration") * 1000).toFixed(1),
  recalcStyleCount: d("RecalcStyleCount"),
  layoutMs: +(d("LayoutDuration") * 1000).toFixed(1),
  layoutCount: d("LayoutCount"),
  scriptMs: +(d("ScriptDuration") * 1000).toFixed(1),
  taskMs: +(d("TaskDuration") * 1000).toFixed(1),
  startW, expectedFinalW: startW + SAMPLES * STEP, ...settle,
};
out.reachedTarget = Math.abs(out.finalW - out.expectedFinalW) < 2;
writeFileSync(`out/${LABEL}.json`, JSON.stringify(out, null, 2));
for (const [k, v] of Object.entries(out)) console.log(`  ${k.padEnd(20)} ${typeof v === "object" ? JSON.stringify(v) : v}`);
await b.close();
