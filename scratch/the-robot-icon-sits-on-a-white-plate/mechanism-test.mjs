// Does <object> isolation cause it? The asset uses mix-blend-mode:multiply x5. Multiply is
// meant to DARKEN against what is behind it — but inside an <object> the SVG is its own
// document, so there is nothing behind it and those shapes render as opaque white.
// Test: inline the same SVG into the page, where multiply CAN reach the dark surface.
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900 });
await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await p.goto("http://127.0.0.1:8790", { waitUntil: "networkidle2" });
await new Promise(r => setTimeout(r, 2500));

const measure = async (sel, tag) => {
  const box = await p.$eval(sel, el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) }; });
  const png = await p.screenshot({ clip: box, encoding: "base64" });
  writeFileSync(`shots/mech-${tag}.png`, Buffer.from(png, "base64"));
  const m = await p.evaluate(async (b64) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
    const ctx = c.getContext("2d", { willReadFrequently: true }); ctx.drawImage(img, 0, 0);
    const { data } = ctx.getImageData(0, 0, c.width, c.height);
    let pale = 0, blue = 0, total = 0, sum = [0,0,0];
    for (let i = 0; i < data.length; i += 4) {
      total++; sum[0]+=data[i]; sum[1]+=data[i+1]; sum[2]+=data[i+2];
      if (data[i] > 170 && data[i+1] > 170 && data[i+2] > 170) pale++;
      if (data[i+2] > 120 && data[i+2] - data[i] > 60) blue++;
    }
    return { palePct: +((pale/total)*100).toFixed(1), bluePct: +((blue/total)*100).toFixed(1), mean: sum.map(v=>Math.round(v/total)).join(",") };
  }, png);
  console.log(`${tag.padEnd(22)} pale ${String(m.palePct).padStart(5)}%  blue ${String(m.bluePct).padStart(5)}%  mean rgb(${m.mean})`);
  return m;
};

await p.evaluate(() => document.querySelector(".tina4-bot").classList.add("thinking"));
await new Promise(r => setTimeout(r, 300));
await measure(".tina4-bot", "object-thinking");

// Inline the very same asset next to it, same size, same opacity.
await p.evaluate(async () => {
  const svg = await (await fetch("/images/tina4-robot-avatar.svg")).text();
  const d = document.createElement("div");
  d.id = "inline-bot";
  d.style.cssText = "position:fixed;left:120px;bottom:28px;width:84px;height:101px;z-index:60;opacity:1;pointer-events:none";
  d.innerHTML = svg;
  const s = d.querySelector("svg");
  s.setAttribute("width", "84"); s.setAttribute("height", "101");
  s.style.cssText = "width:84px;height:101px;display:block";
  document.body.appendChild(d);
});
await new Promise(r => setTimeout(r, 600));
await measure("#inline-bot", "inline-thinking");
console.log("\napp surface behind it: rgb(22,23,26)");
await b.close();
