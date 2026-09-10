// The second user: drags the other way, drags past the limits, and has a smaller window.
// Clamp in PreviewSplitter is Math.max(280, Math.min(innerWidth - 320, startW + dx)).
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8796";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });

for (const [vw, vh, name] of [[1600, 900, "1600x900"], [1100, 700, "1100x700 narrow"]]) {
  for (const [dir, label] of [[-1, "widen (drag left)"], [+1, "shrink (drag right)"]]) {
    const p = await b.newPage();
    await p.setViewport({ width: vw, height: vh });
    await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
    await p.evaluate(() => localStorage.removeItem("t4a.previewWidth"));
    await p.reload({ waitUntil: "networkidle2" });
    await new Promise(r => setTimeout(r, 2000));
    const box = await p.$eval(".preview-splitter", el => { const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; });
    await p.evaluate(() => { window.__t = []; window.__c = null; window.__on = true;
      const el = document.querySelector(".preview-splitter");
      const tk = () => { if (!window.__on) return; window.__t.push([el.getBoundingClientRect().x, window.__c]); requestAnimationFrame(tk); };
      requestAnimationFrame(tk); });
    await p.mouse.move(box.x, box.y); await p.mouse.down();
    // 200 steps of 6px -- far enough to slam into both clamps
    for (let i = 1; i <= 200; i++) {
      const x = box.x + dir * i * 6;
      await p.evaluate((v) => { window.__c = v; }, x);
      await p.mouse.move(x, box.y);
      if (i % 4 === 0) await new Promise(r => setTimeout(r, 1));
    }
    await p.mouse.up();
    await new Promise(r => setTimeout(r, 500));
    const r = await p.evaluate((vw) => {
      window.__on = false;
      const t = window.__t.filter(f => f[1] != null);
      const w = parseFloat(getComputedStyle(document.querySelector(".main")).getPropertyValue("--preview-w"));
      // trail only counts while the cursor is inside the legal range -- past the clamp the
      // splitter is SUPPOSED to stop, so trailing there is correct behaviour, not lag.
      const legal = t.filter(f => f[1] > 320 && f[1] < vw - 280);
      const errs = legal.map(f => Math.abs(f[0] - f[1]));
      return { finalW: Math.round(w), clampLo: 280, clampHi: vw - 320,
        withinClamp: w >= 280 - 1 && w <= vw - 320 + 1,
        meanTrailInLegalRange: errs.length ? +(errs.reduce((s,v)=>s+v,0)/errs.length).toFixed(1) : null,
        legalFrames: errs.length,
        stored: Number(localStorage.getItem("t4a.previewWidth")) };
    }, vw);
    console.log(`  ${name.padEnd(16)} ${label.padEnd(20)} finalW ${String(r.finalW).padStart(4)}  clamp[${r.clampLo}..${r.clampHi}] ok=${r.withinClamp}  trail ${r.meanTrailInLegalRange}px (${r.legalFrames}f)  stored ${r.stored}`);
    await p.close();
  }
}
await b.close();
