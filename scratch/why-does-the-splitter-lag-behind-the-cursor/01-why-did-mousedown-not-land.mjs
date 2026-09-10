import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto("http://127.0.0.1:8795", { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));
console.log(await p.evaluate(() => {
  const host = document.querySelector("preview-splitter");
  const inner = document.querySelector(".preview-splitter");
  const rect = e => e ? (r => ({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}))(e.getBoundingClientRect()) : null;
  const hr = host?.getBoundingClientRect();
  const at = hr ? document.elementFromPoint(hr.x + hr.width/2, hr.y + hr.height/2) : null;
  const main = document.querySelector(".main");
  return {
    hostRect: rect(host), innerRect: rect(inner),
    hostDisplay: host ? getComputedStyle(host).display : null,
    elementAtSplitterCentre: at ? at.tagName.toLowerCase() + "." + (at.className?.baseVal ?? at.className ?? "") : null,
    mainHasInlineStyle: main?.getAttribute("style"),
    whereIsPreviewW: main ? getComputedStyle(main).getPropertyValue("--preview-w").trim() : null,
  };
}));
await b.close();
