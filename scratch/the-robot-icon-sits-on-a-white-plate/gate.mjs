// ui-04 / w-13 — the gate. One command, both properties.
//
//   pale%  share of pixels above 170 on all three channels — the white plate. Must FALL.
//   blue%  share of pixels that are recognisably the robot's blue. Must NOT fall, so a
//          "fix" that deletes or hides the icon cannot pass.
//
// Measured in the .thinking state (opacity 1). At idle the icon is at opacity 0.6 and the
// plate is invisible either way — that is why the first measurement of this bug missed it.
//
//   node gate.mjs                     against whatever is on :8790
//   T4A=http://127.0.0.1:8791 node gate.mjs    against the baseline worktree
//
// PRECONDITION, and it is not optional: a project must be selected. With an empty
// projects root the app raises its "no project" modal, whose .modal-backdrop —
// rgba(20,22,28,0.35) — paints OVER the icon and mutes every pixel under it. Both trees
// then read pale 58.5% / blue 19.7%, and the PATCHED tree FAILS this gate on blue<30
// while being perfectly correct. Measured 2026-09-08. The gate now refuses to report a
// number in that state rather than reporting a false one.
//
// Reference numbers, v0.2.0-290-gd719fc3, 1400x900, chromium 152.0.7977.75,
// project selected, no modal — 3 runs each, spread <=0.1%:
//   <object> (as shipped)   dark/thinking  pale 72.2%  blue 36.3%   FAIL
//   inlined  (the fix)      dark/thinking  pale 10.6%  blue 36.3%   PASS

import { createRequire } from "node:module";
import { writeFileSync, mkdirSync } from "node:fs";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
mkdirSync("shots", { recursive: true });
const HOST = process.env.T4A || "http://127.0.0.1:8790";
const TAG = process.env.TAG || "gate";

const b = await puppeteer.launch({
  executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"],
});

const rows = [];
for (const scheme of ["dark", "light"]) {
  for (const state of ["idle", "thinking"]) {
    const p = await b.newPage();
    await p.setViewport({ width: 1400, height: 900 });
    await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
    await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });
    await new Promise(r => setTimeout(r, 2500));
    await p.evaluate((s) => document.querySelector(".tina4-bot").classList.toggle("thinking", s === "thinking"), state);
    await new Promise(r => setTimeout(r, 500));

    // Anything painted over the icon makes every number below a measurement of that
    // thing, not of the robot. Refuse rather than report.
    const occluder = await p.evaluate(() => {
      const el = document.querySelector(".tina4-bot");
      const r = el.getBoundingClientRect();
      const prev = el.style.pointerEvents; el.style.pointerEvents = "none";
      const over = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      el.style.pointerEvents = prev;
      // An ancestor or a descendant is the icon's own furniture, not an occluder. And an
      // element that paints nothing (transparent background) cannot change a pixel — the
      // icon's own container .rail-list is exactly that, and an earlier version of this
      // guard refused on it.
      if (!over || el.contains(over) || over.contains(el)) return null;
      const cs = getComputedStyle(over);
      const alpha = (cs.backgroundColor.match(/^rgba?\([^)]*?,\s*([\d.]+)\)$/) ?? [, "1"])[1];
      if (cs.backgroundColor === "transparent" || Number(alpha) === 0) return null;
      return { sel: over.tagName.toLowerCase() + "." + (over.className?.baseVal ?? over.className ?? "?"), bg: cs.backgroundColor, opacity: cs.opacity };
    });
    if (occluder) {
      console.error(`\nREFUSING TO MEASURE: <${occluder.sel}> is painted over the icon (bg ${occluder.bg}).`);
      console.error(`Every pixel below would be that element, not the robot. Select a project so the`);
      console.error(`"no project" modal is down, then re-run. See the PRECONDITION note at the top.`);
      await b.close(); process.exit(2);
    }

    const box = await p.$eval(".tina4-bot", el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) }; });
    const png = await p.screenshot({ clip: box, encoding: "base64" });
    writeFileSync(`shots/${TAG}-${scheme}-${state}.png`, Buffer.from(png, "base64"));

    const m = await p.evaluate(async (b64) => {
      const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
      const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
      const ctx = c.getContext("2d", { willReadFrequently: true }); ctx.drawImage(img, 0, 0);
      const { data } = ctx.getImageData(0, 0, c.width, c.height);
      let pale = 0, blue = 0, total = 0, sum = [0, 0, 0];
      for (let i = 0; i < data.length; i += 4) {
        total++; sum[0] += data[i]; sum[1] += data[i + 1]; sum[2] += data[i + 2];
        if (data[i] > 170 && data[i + 1] > 170 && data[i + 2] > 170) pale++;
        if (data[i + 2] > 120 && data[i + 2] - data[i] > 60) blue++;
      }
      return { palePct: +((pale / total) * 100).toFixed(1), bluePct: +((blue / total) * 100).toFixed(1), mean: sum.map(v => Math.round(v / total)).join(",") };
    }, png);

    // Did the icon actually render? An empty box passes "pale is low" trivially.
    const kids = await p.$eval(".tina4-bot", el => ({ tag: el.tagName.toLowerCase(), children: el.children.length, first: el.firstElementChild?.tagName?.toLowerCase() ?? null }));
    rows.push({ scheme, state, ...m, ...kids });
    console.log(`${scheme.padEnd(5)} ${state.padEnd(9)} pale ${String(m.palePct).padStart(5)}%  blue ${String(m.bluePct).padStart(5)}%  mean rgb(${m.mean})  <${kids.tag}> ${kids.children} child ${kids.first ?? "-"}`);
    await p.close();
  }
}
await b.close();
writeFileSync(`shots/${TAG}.json`, JSON.stringify(rows, null, 2));

const dt = rows.find(r => r.scheme === "dark" && r.state === "thinking");
const ok = dt.palePct < 20 && dt.bluePct > 30 && dt.children > 0;
console.log(`\ndark/thinking: pale ${dt.palePct}% (want <20) · blue ${dt.bluePct}% (want >30) · children ${dt.children} (want >0)  ${ok ? "PASS" : "FAIL"}`);
process.exit(ok ? 0 : 1);
