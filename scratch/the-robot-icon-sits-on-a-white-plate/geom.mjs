// Why do the gate numbers move between app states? Measure the box, not the pixels.
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
for (const [host, tag] of [["http://127.0.0.1:8791","BASE empty-root"],["http://127.0.0.1:8792","PATCH empty-root"],
                           ["http://127.0.0.1:8790","PATCH your-root"]]) {
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 900 });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
  await p.goto(host, { waitUntil: "networkidle2", timeout: 30000 });
  await new Promise(r => setTimeout(r, 2500));
  await p.evaluate(() => document.querySelector(".tina4-bot").classList.add("thinking"));
  await new Promise(r => setTimeout(r, 500));
  const g = await p.evaluate(() => {
    const el = document.querySelector(".tina4-bot");
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    // what is painted directly behind the icon's centre?
    el.style.pointerEvents = "none";
    const under = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
    el.style.pointerEvents = "";
    return {
      box: `${Math.round(r.width)}x${Math.round(r.height)} at ${Math.round(r.x)},${Math.round(r.y)}`,
      opacity: cs.opacity, tag: el.tagName.toLowerCase(),
      behind: under ? under.tagName.toLowerCase() + "." + (under.className?.baseVal ?? under.className ?? "") : null,
      behindBg: under ? getComputedStyle(under).backgroundColor : null,
      bodyBg: getComputedStyle(document.body).backgroundColor,
      project: document.querySelector(".project-pill,[class*=project]")?.textContent?.trim().slice(0,40) ?? "(none)",
      vw: innerWidth, vh: innerHeight,
    };
  });
  console.log(`${tag.padEnd(18)} box ${g.box}  opacity ${g.opacity}  <${g.tag}>`);
  console.log(`${"".padEnd(18)} body ${g.bodyBg}  behind ${g.behind} bg ${g.behindBg}`);
  console.log(`${"".padEnd(18)} project ${g.project}`);
  await p.close();
}
await b.close();
