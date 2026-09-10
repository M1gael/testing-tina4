// The picture, for a human. Same crop, same state (.thinking, the state the plate shows in),
// dark theme, both trees.
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
for (const [host, tag] of [["http://127.0.0.1:8791", "SHIPPED-object"], ["http://127.0.0.1:8790", "FIXED-inline"]]) {
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 900 });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
  await p.goto(host, { waitUntil: "networkidle2", timeout: 30_000 });
  await new Promise(r => setTimeout(r, 3000));
  await p.evaluate(() => document.querySelector(".tina4-bot").classList.add("thinking"));
  await new Promise(r => setTimeout(r, 1200));
  writeFileSync(`shots/side-${tag}.png`, Buffer.from(await p.screenshot({ clip: { x: 0, y: 640, width: 320, height: 260 }, encoding: "base64" }), "base64"));
  await p.close();
  console.log(`shots/side-${tag}.png`);
}
await b.close();
