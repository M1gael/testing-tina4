// Read the header out of the running harness with a real browser. Port and expectations from argv.
import puppeteer from "/var/home/work/gitdir/tina4-simple-agent-work/scratch/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";
const port = process.argv[2];
const browser = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: true, args: ["--no-sandbox"] });
const page = await browser.newPage();
const errs = []; page.on("pageerror", e => errs.push(String(e.message).split("\n")[0]));
await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));
const out = await page.evaluate(() => {
  const chip = document.querySelector(".model-chip");
  return {
    chipText: chip ? chip.textContent.replace(/\s+/g, " ").trim() : null,
    chipTitle: chip ? chip.getAttribute("title") : null,
    roleSpans: [...document.querySelectorAll(".model-chip .mc-role")].map(e => e.textContent.trim()),
    statsText: document.querySelector(".session-stats")?.textContent.replace(/\s+/g, " ").trim() ?? null,
    rateSpan: document.querySelector(".session-stats .rate")?.textContent.trim() ?? null,
  };
});
out.api = await page.evaluate(async () => { const j = await (await fetch("/api/model")).json(); return { model: j.model, thinker: j.thinker?.model }; });
console.log(JSON.stringify(out, null, 1));
console.log("pageerrors:", errs.slice(0, 3));
await browser.close();
