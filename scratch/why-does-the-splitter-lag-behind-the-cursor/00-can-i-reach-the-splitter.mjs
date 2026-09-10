// Before measuring anything: is the splitter reachable, and what opens the preview?
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8795";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));
console.log(await p.evaluate(() => ({
  splitter: !!document.querySelector("preview-splitter"),
  mainClass: document.querySelector(".main")?.className ?? null,
  previewW: getComputedStyle(document.querySelector(".main") ?? document.body).getPropertyValue("--preview-w").trim(),
  iframes: document.querySelectorAll("iframe.preview-frame").length,
  stored: localStorage.getItem("t4a.previewWidth"),
  buttons: [...document.querySelectorAll("button")].map(x => (x.title||x.textContent||"").trim().slice(0,26)).filter(Boolean).slice(0,40),
})));
await b.close();
