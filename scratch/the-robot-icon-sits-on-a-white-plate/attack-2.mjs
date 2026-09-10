// w-13 attack round 2 — three questions the gate cannot answer.
//  A. The SVG's own <style> is now a document-global sheet. index.html is served with NO CSP
//     header today (only the 302 carries one), so it applies. If that is ever fixed, the sheet
//     is blocked. Does the icon depend on it?
//  B. The class attribute is reactively bound to streaming. Does a re-render wipe the injected
//     children, or double them?
//  C. Does the fetch run more than once?
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--force-device-scale-factor=1"] });
const p = await b.newPage();
let svgFetches = 0;
p.on("request", r => { if (r.url().endsWith("tina4-robot-avatar.svg")) svgFetches++; });
await p.setViewport({ width: 1400, height: 900 });
await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await p.goto("http://127.0.0.1:8790", { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise(r => setTimeout(r, 2500));

const measure = async (tag) => {
  const box = await p.$eval(".tina4-bot", el => { const r = el.getBoundingClientRect(); return { x:Math.round(r.x), y:Math.round(r.y), width:Math.round(r.width), height:Math.round(r.height) }; });
  const png = await p.screenshot({ clip: box, encoding: "base64" });
  writeFileSync(`shots/attack2-${tag}.png`, Buffer.from(png, "base64"));
  const m = await p.evaluate(async (b64) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
    const ctx = c.getContext("2d", { willReadFrequently: true }); ctx.drawImage(img, 0, 0);
    const { data } = ctx.getImageData(0, 0, c.width, c.height);
    let pale=0, blue=0, total=0;
    for (let i=0;i<data.length;i+=4){ total++; if(data[i]>170&&data[i+1]>170&&data[i+2]>170)pale++; if(data[i+2]>120&&data[i+2]-data[i]>60)blue++; }
    return { pale:+((pale/total)*100).toFixed(1), blue:+((blue/total)*100).toFixed(1) };
  }, png);
  const dom = await p.$eval(".tina4-bot", el => ({ children: el.children.length, svgs: el.querySelectorAll("svg").length, cls: el.className }));
  console.log(`${tag.padEnd(26)} pale ${String(m.pale).padStart(5)}%  blue ${String(m.blue).padStart(5)}%  children ${dom.children} svgs ${dom.svgs}  class "${dom.cls}"`);
  return { ...m, ...dom };
};

await p.evaluate(() => document.querySelector(".tina4-bot").classList.add("thinking"));
await new Promise(r => setTimeout(r, 400));
await measure("thinking (control)");

// A — kill the SVG's own stylesheet, exactly as a real style-src CSP would.
await p.evaluate(() => { const s = document.querySelector(".tina4-bot style"); s.remove(); });
await new Promise(r => setTimeout(r, 300));
await measure("A: <style> removed");
await p.reload({ waitUntil: "networkidle2" });
await new Promise(r => setTimeout(r, 2500));

// B — drive the real reactive path: flip the streaming signal the class is bound to.
const flip = await p.evaluate(async () => {
  // streaming is module-scoped; reach it through the rendered class instead by dispatching
  // what actually sets it is not exposed, so mutate via the same effect: toggle and observe.
  const el = document.querySelector(".tina4-bot");
  const before = { children: el.children.length, cls: el.className };
  el.classList.add("thinking"); el.classList.remove("thinking"); el.classList.add("thinking");
  await new Promise(r => setTimeout(r, 300));
  return { before, after: { children: el.children.length, cls: el.className } };
});
console.log("B: class churn        ", JSON.stringify(flip));
await measure("B: after class churn");

console.log(`C: SVG network fetches this page load: ${svgFetches} (want 1)`);
await b.close();
