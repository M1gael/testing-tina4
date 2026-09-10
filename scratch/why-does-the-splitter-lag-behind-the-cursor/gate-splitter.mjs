// w-15 / ui-01 — THE GATE. Written before the fix.
//
// Claim: during a splitter drag the rendered splitter tracks the cursor, and stops when the
// mouse stops -- WITHOUT killing the preview open/close animation.
//
//   1. meanTrailPx        < 12    the pane follows the cursor, not 0.25s behind it
//   2. settleAfterUpMs    < 60    it stops when the mouse stops
//   3. |finalX-targetX|  <= 6     ANTI-STUB: it still actually resizes to where you dragged
//   4. stored == finalW           ANTI-STUB: the width still PERSISTS. Deleting the signal write
//                                 or the localStorage effect would satisfy 1-3.
//   5. hide/show round-trips      REGRESSION: hiding the preview gives the centre column the full
//                                 width, and showing it restores the dragged width.
//
// An earlier draft asserted "hiding the preview still animates (>=120ms)". That check FAILED on
// the untouched tree -- 11ms, a 765px jump -- because grid-template-columns only interpolates
// when the TRACK COUNT matches, and every class toggle here changes the count. The 0.25s ease
// therefore animates nothing except a --preview-w change, and the only writer of --preview-w is
// the drag. The assumption that deleting it would cost a wanted animation was false.
//
//   T4A=http://127.0.0.1:8795 node gate-splitter.mjs
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8795";
const SAMPLES = 60, STEP = 4, GAP = 8;

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));
const CPU = Number(process.env.CPU || 1);
if (CPU > 1) { const c = await p.target().createCDPSession(); await c.send("Emulation.setCPUThrottlingRate", { rate: CPU }); }

const box = await p.$eval(".preview-splitter", el => { const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; });
if (!(box.x > 0)) { console.error("REFUSING: splitter has no box (preview closed?)"); await b.close(); process.exit(2); }

await p.evaluate(() => { window.__cursorX = null; window.__trace = []; window.__on = true;
  const el = document.querySelector(".preview-splitter");
  const tick = () => { if (!window.__on) return;
    window.__trace.push([performance.now(), el.getBoundingClientRect().x, window.__cursorX]); requestAnimationFrame(tick); };
  requestAnimationFrame(tick); });

await p.mouse.move(box.x, box.y); await p.mouse.down();
for (let i = 1; i <= SAMPLES; i++) {
  const x = box.x - i * STEP;
  await p.evaluate((v) => { window.__cursorX = v; }, x);
  await p.mouse.move(x, box.y);
  await new Promise(r => setTimeout(r, GAP));
}
const tLast = await p.evaluate(() => performance.now());
await p.mouse.up();
await new Promise(r => setTimeout(r, 1200));

const drag = await p.evaluate((tL) => {
  window.__on = false;
  const tr = window.__trace.filter(f => f[2] != null);
  const during = tr.filter(f => f[0] <= tL), after = tr.filter(f => f[0] > tL);
  const errs = during.map(f => Math.abs(f[1] - f[2]));
  let settle = 0;
  for (let i = after.length - 1; i > 0; i--) if (Math.abs(after[i][1] - after[i-1][1]) > 0.5) { settle = Math.round(after[i][0] - tL); break; }
  return { frames: during.length,
    meanTrailPx: +(errs.reduce((s,v)=>s+v,0)/(errs.length||1)).toFixed(1),
    maxTrailPx: +Math.max(...errs, 0).toFixed(1),
    settleAfterUpMs: settle,
    finalX: Math.round(tr.at(-1)[1]), targetX: Math.round(during.at(-1)[2]) };
}, tLast);

// 4/5. Persistence, and hide/show round-trip.
const toggle = await p.evaluate(async () => {
  const sleep = () => new Promise(r => setTimeout(r, 600));
  const stored = Number(localStorage.getItem("t4a.previewWidth"));
  const px = () => { const m = document.querySelector(".main"); return parseFloat(getComputedStyle(m).getPropertyValue("--preview-w")); };
  const widthNow = px();
  const centre = () => document.querySelector(".center-col").getBoundingClientRect().width;
  const find = (t) => [...document.querySelectorAll("button")].find(x => (x.title||"").trim() === t);
  const before = centre();
  const hide = find("Hide preview"); if (!hide) return { stored, widthNow, roundTrip: "no Hide button" };
  hide.click(); await sleep();
  const hidden = centre();
  const show = find("Show preview") || find("Hide preview"); show.click(); await sleep();
  return { stored, widthNow, centreBefore: Math.round(before), centreHidden: Math.round(hidden),
           centreAfter: Math.round(centre()), widthAfter: px(),
           grewWhenHidden: hidden > before + 100, restored: Math.abs(px() - widthNow) < 2 };
});

const r = { host: HOST, cpu: CPU, ...drag, ...toggle };
for (const [k,v] of Object.entries(r)) console.log(`  ${k.padEnd(18)} ${v}`);
const checks = [
  ["1 meanTrailPx    < 12", r.meanTrailPx < 12],
  ["2 settleAfterUp  < 60", r.settleAfterUpMs < 60],
  ["3 reaches target <= 6", Math.abs(r.finalX - r.targetX) <= 6],
  ["4 width persisted", Math.abs(r.stored - r.widthNow) < 2],
  ["5 hide/show round-trips", r.grewWhenHidden === true && r.restored === true],
];
console.log();
for (const [n, ok] of checks) console.log(`  ${ok ? "ok  " : "FAIL"}  ${n}`);
const pass = checks.every(c => c[1]);
console.log(`\n  ${pass ? "PASS" : "FAIL"}`);
await b.close();
process.exit(pass ? 0 : 1);
