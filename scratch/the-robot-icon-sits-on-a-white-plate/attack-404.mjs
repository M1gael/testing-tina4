// w-13 attack, the second user — the SVG request fails (offline, cache miss, a 404 after the
// asset is renamed). The <object> version degraded to an empty box. Does the inlined one leave
// the shell working, or does an unhandled rejection take something with it?
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu"] });
const p = await b.newPage();
const errs = [];
p.on("pageerror", e => errs.push("pageerror: " + e.message));
p.on("console", m => { if (m.type() === "error") errs.push("console: " + m.text()); });
await p.setRequestInterception(true);
p.on("request", r => r.url().endsWith("tina4-robot-avatar.svg") ? r.abort("failed") : r.continue());
await p.setViewport({ width: 1400, height: 900 });
await p.goto("http://127.0.0.1:8790", { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise(r => setTimeout(r, 3000));
const r = await p.evaluate(() => ({
  botChildren: document.querySelector(".tina4-bot")?.children.length ?? -1,
  shell: !!document.querySelector(".shell"),
  topbar: !!document.querySelector(".topbar"),
  composer: !!document.querySelector(".composer"),
  projectPill: document.querySelector(".project-pill")?.textContent?.trim() ?? null,
}));
console.log("with the SVG request aborted:", JSON.stringify(r));
// A failed fetch logs a net::ERR line; what matters is that nothing else broke.
console.log("errors:", errs.filter(e => !/tina4-robot-avatar|Failed to load resource/.test(e)).length ? errs : "(only the expected network failure)");
await b.close();
process.exit(r.shell && r.topbar && r.composer ? 0 : 1);
