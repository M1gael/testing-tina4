// ui-04 / w-13 — the tina4 robot bottom-left reads as a white plate on a dark window.
//
// Screenshots the robot's box in dark and light, and measures it, so the gate is a number rather
// than my eye:
//   whitePct   share of pixels within 12/255 of pure white
//   corners    the four corner pixels of the box — background, not robot
//   inkPct     share of pixels near the robot's own blue (#020fb5), so a "fix" that deletes the
//              icon does not pass
//
// Reads the screenshot back through a canvas in the page — no image library needed.
//
//   node shoot.mjs <label>          e.g. node shoot.mjs before

import { createRequire } from "node:module";
import { writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HARNESS = "/var/home/work/gitdir/tina4-simple-agent-work/scratch/";
const puppeteer = createRequire(HARNESS + "package.json")("puppeteer-core");

const HERE = path.dirname(fileURLToPath(import.meta.url));
const LABEL = process.argv[2] || "shot";
const HOST = "http://127.0.0.1:8790";
mkdirSync(path.join(HERE, "shots"), { recursive: true });

const browser = await puppeteer.launch({
  executablePath: "/usr/bin/chromium-browser",
  headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"],
});

const results = [];
for (const scheme of ["dark", "light"]) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });
  await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
  await page.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });
  await new Promise((r) => setTimeout(r, 2500)); // the <object> loads its own document

  const box = await page.$eval(".tina4-bot", (el) => {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) };
  });
  // A margin so the app surface immediately around the icon is in frame too.
  const clip = { x: Math.max(0, box.x - 10), y: Math.max(0, box.y - 10), width: box.width + 20, height: box.height + 20 };

  const png = await page.screenshot({ clip, encoding: "base64" });
  writeFileSync(path.join(HERE, "shots", `${LABEL}-${scheme}.png`), Buffer.from(png, "base64"));

  const measured = await page.evaluate(async (b64) => {
    const img = new Image();
    img.src = "data:image/png;base64," + b64;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    const ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    const { data, width, height } = ctx.getImageData(0, 0, c.width, c.height);
    const px = (x, y) => { const i = (y * width + x) * 4; return [data[i], data[i + 1], data[i + 2], data[i + 3]]; };
    let white = 0, ink = 0, total = 0;
    for (let i = 0; i < data.length; i += 4) {
      const [r, g, bl, a] = [data[i], data[i + 1], data[i + 2], data[i + 3]];
      if (a < 8) continue;
      total++;
      if (r > 243 && g > 243 && bl > 243) white++;
      if (Math.abs(r - 2) < 48 && Math.abs(g - 15) < 48 && Math.abs(bl - 181) < 60) ink++;
    }
    return {
      size: `${width}x${height}`,
      whitePct: +((white / total) * 100).toFixed(1),
      inkPct: +((ink / total) * 100).toFixed(1),
      corners: [px(1, 1), px(width - 2, 1), px(1, height - 2), px(width - 2, height - 2)].map((c) => `rgb(${c[0]},${c[1]},${c[2]})`),
      bodyBg: getComputedStyle(document.body).backgroundColor,
    };
  }, png);

  results.push({ scheme, box, ...measured });
  console.log(
    `${scheme.padEnd(5)}  box ${box.width}x${box.height} at ${box.x},${box.y}` +
    `  · white ${String(measured.whitePct).padStart(5)}%  robot-blue ${String(measured.inkPct).padStart(5)}%` +
    `\n       body bg ${measured.bodyBg}` +
    `\n       corners ${measured.corners.join("  ")}`
  );
  await page.close();
}

await browser.close();
writeFileSync(path.join(HERE, "shots", `${LABEL}.json`), JSON.stringify(results, null, 2));
console.log(`\nshots/${LABEL}-dark.png, shots/${LABEL}-light.png, shots/${LABEL}.json`);
