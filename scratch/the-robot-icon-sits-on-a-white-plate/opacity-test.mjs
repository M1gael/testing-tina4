import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900 });
await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await p.goto("http://127.0.0.1:8790", { waitUntil: "networkidle2" });
await new Promise(r => setTimeout(r, 2500));

for (const state of ["idle", "thinking"]) {
  await p.evaluate((s) => {
    const el = document.querySelector(".tina4-bot");
    el.classList.toggle("thinking", s === "thinking");
  }, state);
  await new Promise(r => setTimeout(r, 400));
  const box = await p.$eval(".tina4-bot", el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) }; });
  const clip = { x: box.x, y: box.y, width: box.width, height: box.height };
  const png = await p.screenshot({ clip, encoding: "base64" });
  writeFileSync(`shots/state-${state}.png`, Buffer.from(png, "base64"));
  const m = await p.evaluate(async (b64) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
    const ctx = c.getContext("2d", { willReadFrequently: true }); ctx.drawImage(img, 0, 0);
    const { data } = ctx.getImageData(0, 0, c.width, c.height);
    let pale = 0, total = 0, sum = [0,0,0];
    for (let i = 0; i < data.length; i += 4) {
      total++; sum[0]+=data[i]; sum[1]+=data[i+1]; sum[2]+=data[i+2];
      if (data[i] > 170 && data[i+1] > 170 && data[i+2] > 170) pale++;
    }
    return { palePct: +((pale/total)*100).toFixed(1), mean: sum.map(v => Math.round(v/total)).join(",") };
  }, png);
  const op = await p.evaluate(() => getComputedStyle(document.querySelector(".tina4-bot")).opacity);
  console.log(`${state.padEnd(9)} opacity ${op}  · pale pixels ${String(m.palePct).padStart(5)}%  · mean rgb(${m.mean})`);
}
console.log("app surface for comparison: rgb(22,23,26) body / rgb(35,36,39) panel");
await b.close();
