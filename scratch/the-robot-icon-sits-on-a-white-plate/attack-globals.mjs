// w-13 attack — the SVGator player used to run inside the <object>'s own document. Inlined, it
// runs in the page's document and its globals land on the page's window. What appears, and does
// it collide with anything the app owns?
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu"] });
const grab = async (host) => {
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 900 });
  await p.goto(host, { waitUntil: "networkidle2", timeout: 30_000 });
  await new Promise(r => setTimeout(r, 3000));
  const r = await p.evaluate(() => ({
    keys: Object.getOwnPropertyNames(window).filter(k => !/^(webkit|chrome)/.test(k)),
    listeners: typeof getEventListeners === "function" ? "n/a" : "n/a",
    rafPending: !!window.requestAnimationFrame,
  }));
  await p.close(); return r;
};
const base = await grab("http://127.0.0.1:8791");
const ours = await grab("http://127.0.0.1:8790");
const added = ours.keys.filter(k => !base.keys.includes(k));
const removed = base.keys.filter(k => !ours.keys.includes(k));
console.log("globals added by inlining:  ", added.length ? added : "(none)");
console.log("globals removed:            ", removed.length ? removed : "(none)");
await b.close();
