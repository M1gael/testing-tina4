import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
for (const scheme of ["dark","light"]) {
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 860 });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
  await p.goto(process.env.T4A || "http://127.0.0.1:8796", { waitUntil: "networkidle2", timeout: 30000 });
  await new Promise(r => setTimeout(r, 2200));
  await p.evaluate(() => [...document.querySelectorAll("button")].find(x=>(x.textContent||"").trim().toLowerCase()==="new session")?.click());
  await new Promise(r => setTimeout(r, 700));
  const box = await p.evaluate(() => { const m=document.querySelector(".modal"); const r=m.getBoundingClientRect();
    return { x:Math.max(0,Math.round(r.x)-30), y:Math.max(0,Math.round(r.y)-30), width:Math.round(r.width)+60, height:Math.round(r.height)+60 }; });
  writeFileSync(`shots/new-session-modal-${scheme}.png`, Buffer.from(await p.screenshot({ clip: box, encoding: "base64" }), "base64"));
  console.log(`  shots/new-session-modal-${scheme}.png  ${box.width}x${box.height}`);
  await p.close();
}
await b.close();
