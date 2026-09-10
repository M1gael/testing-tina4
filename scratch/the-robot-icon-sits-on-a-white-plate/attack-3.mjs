// One page load, count the SVG requests and the injected DOM. attack-2 reloads once, so its
// counter spans two loads — this one does not.
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu"] });
const p = await b.newPage();
let n = 0; const errs = [];
p.on("request", r => { if (r.url().endsWith("tina4-robot-avatar.svg")) n++; });
p.on("pageerror", e => errs.push(String(e)));
p.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
await p.setViewport({ width: 1400, height: 900 });
await p.goto("http://127.0.0.1:8790", { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise(r => setTimeout(r, 3000));
const dom = await p.$eval(".tina4-bot", el => ({ tag: el.tagName.toLowerCase(), role: el.getAttribute("role"), label: el.getAttribute("aria-label"), children: el.children.length, svgs: el.querySelectorAll("svg").length }));
console.log(`svg requests on one load: ${n} (want 1)`);
console.log("bot element:", JSON.stringify(dom));
console.log("console errors / page errors:", errs.length ? errs : "(none)");
await b.close();
process.exit(n === 1 && dom.svgs === 1 && errs.length === 0 ? 0 : 1);
