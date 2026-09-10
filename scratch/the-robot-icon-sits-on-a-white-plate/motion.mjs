// w-13 — the gate was blind to motion. The SVG carries no SMIL and no CSS keyframes: it has one
// inline <script> (SVGator, 20 references) and that script is the whole animation. innerHTML does
// not execute injected <script>, so an inlined copy is a still image unless the script is
// re-created. This measures motion instead of asserting it: N frames of the icon's box, each
// compared pixel-by-pixel to the first.
//
//   T4A=http://127.0.0.1:8791 node motion.mjs      the shipped <object> version
//   node motion.mjs                                whatever is on :8790
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8790";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900 });
await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise(r => setTimeout(r, 3000));
await p.evaluate(() => document.querySelector(".tina4-bot").classList.add("thinking"));
await new Promise(r => setTimeout(r, 1200));   // let the 0.35s opacity transition finish first

const box = await p.$eval(".tina4-bot", el => { const r = el.getBoundingClientRect(); return { x:Math.round(r.x), y:Math.round(r.y), width:Math.round(r.width), height:Math.round(r.height) }; });
const frames = [];
for (let i = 0; i < 12; i++) { frames.push(await p.screenshot({ clip: box, encoding: "base64" })); await new Promise(r => setTimeout(r, 250)); }

const diffs = await p.evaluate(async (fr) => {
  const load = async (b64) => { const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
    const x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(img, 0, 0);
    return x.getImageData(0, 0, c.width, c.height).data; };
  // Consecutive frames, not all-vs-first: a one-off step (the opacity transition) would make
  // every all-vs-first comparison identical and read as motion. It is not.
  const out = []; let prev = await load(fr[0]);
  for (let i = 1; i < fr.length; i++) {
    const d = await load(fr[i]); let n = 0;
    for (let j = 0; j < d.length; j += 4) if (Math.abs(d[j]-prev[j]) + Math.abs(d[j+1]-prev[j+1]) + Math.abs(d[j+2]-prev[j+2]) > 24) n++;
    out.push(+((n / (d.length/4)) * 100).toFixed(2)); prev = d;
  }
  return out;
}, frames);

const peak = Math.max(...diffs);
console.log(`consecutive-frame change, % pixels: ${diffs.join(" ")}`);
console.log(`peak ${peak}%  ${peak > 1 ? "MOVING" : "STILL"}`);
await b.close();
process.exit(peak > 1 ? 0 : 1);
