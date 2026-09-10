// "Smooth but very delayed" is a LATENCY symptom, not a framerate one. So measure the thing the
// operator sees: how far the rendered splitter trails the cursor, and how long it keeps moving
// after the mouse stops.
//
// Reads getBoundingClientRect() per frame, which forces layout -- deliberate, it is the
// measurement, and it perturbs both trees identically.
//
//   T4A=http://127.0.0.1:8795 node lag.mjs <label>
import { createRequire } from "node:module";
import { writeFileSync, mkdirSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
mkdirSync("out", { recursive: true });
const HOST = process.env.T4A || "http://127.0.0.1:8795";
const LABEL = process.argv[2] || "lag";
const SAMPLES = Number(process.env.SAMPLES || 60), STEP = Number(process.env.STEP || 4), GAP = Number(process.env.GAP || 8);

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));
const cdp = await p.target().createCDPSession();
const CPU = Number(process.env.CPU || 1);
if (CPU > 1) await cdp.send("Emulation.setCPUThrottlingRate", { rate: CPU });

const box = await p.$eval(".preview-splitter", el => { const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; });
if (!(box.x > 0)) { console.error("no splitter box"); await b.close(); process.exit(2); }

// Per-frame: where the splitter is actually drawn, and where the cursor was told to be.
await p.evaluate(() => {
  window.__cursorX = null; window.__trace = []; window.__on = true;
  const el = document.querySelector(".preview-splitter");
  const tick = () => { if (!window.__on) return;
    window.__trace.push([performance.now(), el.getBoundingClientRect().x, window.__cursorX]);
    requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
});

await p.mouse.move(box.x, box.y);
await p.mouse.down();
for (let i = 1; i <= SAMPLES; i++) {
  const x = box.x - i * STEP;
  await p.evaluate((v) => { window.__cursorX = v; }, x);
  await p.mouse.move(x, box.y);
  await new Promise(r => setTimeout(r, GAP));
}
const tLastInput = await p.evaluate(() => performance.now());
await p.mouse.up();
await new Promise(r => setTimeout(r, 1200));   // let any transition finish

const res = await p.evaluate((tLast) => {
  window.__on = false;
  const tr = window.__trace.filter(f => f[2] != null);
  const during = tr.filter(f => f[0] <= tLast);
  const after  = tr.filter(f => f[0] >  tLast);
  const errs = during.map(f => Math.abs(f[1] - f[2]));
  const finalX = tr.length ? tr.at(-1)[1] : null;
  // when did it stop moving after the last input?
  let settle = 0;
  for (let i = after.length - 1; i > 0; i--) {
    if (Math.abs(after[i][1] - after[i-1][1]) > 0.5) { settle = Math.round(after[i][0] - tLast); break; }
  }
  const mean = a => a.length ? +(a.reduce((s,v)=>s+v,0)/a.length).toFixed(1) : null;
  return {
    framesDuringDrag: during.length,
    meanTrailPx: mean(errs),
    maxTrailPx: errs.length ? +Math.max(...errs).toFixed(1) : null,
    trailAtEndPx: during.length ? +Math.abs(during.at(-1)[1] - during.at(-1)[2]).toFixed(1) : null,
    settleAfterMouseUpMs: settle,
    finalX: finalX == null ? null : Math.round(finalX),
    targetX: during.length ? Math.round(during.at(-1)[2]) : null,
  };
}, tLastInput);

const out = { label: LABEL, host: HOST, cpuThrottle: CPU, samples: SAMPLES, stepPx: STEP, gapMs: GAP, ...res };
writeFileSync(`out/${LABEL}.json`, JSON.stringify(out, null, 2));
for (const [k,v] of Object.entries(out)) console.log(`  ${k.padEnd(22)} ${v}`);
await b.close();
