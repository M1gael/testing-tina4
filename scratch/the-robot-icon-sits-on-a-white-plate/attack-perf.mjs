// w-13 attack — the animation used to run inside the <object>'s own document, so its style and
// layout work was that document's. Inlined, it animates in the page. w-15 already established
// that this page's cost is dominated by style recalculation, so measure whether the icon now
// adds to it. 6 seconds idle, no interaction, both trees.
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu"] });
const run = async (host, label) => {
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 900 });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
  await p.goto(host, { waitUntil: "networkidle2", timeout: 30_000 });
  await new Promise(r => setTimeout(r, 3000));
  const cdp = await p.target().createCDPSession();
  await cdp.send("Performance.enable");
  const pick = (m) => Object.fromEntries(m.metrics.filter(x => /RecalcStyle|Layout|ScriptDuration|TaskDuration/.test(x.name)).map(x => [x.name, x.value]));
  const a = pick(await cdp.send("Performance.getMetrics"));
  await new Promise(r => setTimeout(r, 6000));
  const z = pick(await cdp.send("Performance.getMetrics"));
  const d = Object.fromEntries(Object.keys(z).map(k => [k, +(z[k] - a[k]).toFixed(3)]));
  console.log(`${label.padEnd(22)} style ${String(d.RecalcStyleDuration).padStart(7)}s  layout ${String(d.LayoutDuration).padStart(7)}s  script ${String(d.ScriptDuration).padStart(7)}s  task ${String(d.TaskDuration).padStart(7)}s  recalcs ${d.RecalcStyleCount}  layouts ${d.LayoutCount}`);
  await p.close();
};
await run("http://127.0.0.1:8791", "baseline <object>");
await run("http://127.0.0.1:8790", "patched inline");
await b.close();
