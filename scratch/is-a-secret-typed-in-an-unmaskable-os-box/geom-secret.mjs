// Does the `display: contents` entry for secret-value-modal do anything measurable, or is it dead
// weight carried for consistency? Component gating could not answer it -- every functional check
// passed with the line removed -- so measure the layout instead of arguing about it.
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8796";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--hide-scrollbars"] });
const p = await b.newPage(); await p.setViewport({ width: 1400, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await p.click('button.cog-btn[title="Edit current project"]'); await new Promise(r=>setTimeout(r,900));
const before = await p.evaluate(() => { const m = document.querySelector(".main"); const r = m?.getBoundingClientRect(); return r ? { top: Math.round(r.top), height: Math.round(r.height) } : null; });
await p.evaluate(() => {
  const row = document.querySelector(".secret-row");
  [...(row?.querySelectorAll("button")||[])].find(x=>/replace/i.test(x.textContent))?.click();
});
await new Promise(r=>setTimeout(r,600));
const out = await p.evaluate(() => {
  const el = document.querySelector("secret-value-modal");
  const r = el?.getBoundingClientRect();
  const m = document.querySelector(".main")?.getBoundingClientRect();
  return {
    elementExists: !!el,
    computedDisplay: el ? getComputedStyle(el).display : null,
    elementBox: r ? { w: Math.round(r.width), h: Math.round(r.height) } : null,
    mainTop: m ? Math.round(m.top) : null,
    mainHeight: m ? Math.round(m.height) : null,
  };
});
console.log("  .main before opening ", JSON.stringify(before));
console.log("  while dialog is open ", JSON.stringify(out));
console.log("");
const shifted = before && out.mainTop !== null && (out.mainTop !== before.top || out.mainHeight !== before.height);
console.log(out.computedDisplay === "contents"
  ? "  display:contents IS applied -- the element creates no box"
  : `  display is ${JSON.stringify(out.computedDisplay)} -- the element DOES create a box: ${JSON.stringify(out.elementBox)}`);
console.log(shifted ? `  LAYOUT SHIFTED: .main moved ${before.top} -> ${out.mainTop}, height ${before.height} -> ${out.mainHeight}`
                    : "  layout unchanged behind the dialog");
await b.close();
