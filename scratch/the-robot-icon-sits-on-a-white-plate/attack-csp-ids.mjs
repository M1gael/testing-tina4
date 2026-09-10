// w-13 attack — the inline SVG carries <style>#emjSaVDW3zs2{display:none!important}</style>.
// Inside an <object> that stylesheet was scoped to the embedded document. Inlined it becomes a
// document-global stylesheet, and the page is served under Content-Security-Policy
// "default-src 'self'" with no style-src 'unsafe-inline'. Two questions:
//   1. does CSP block the injected <style>, un-hiding an element the artwork means to hide?
//   2. do any of the SVG's 82 ids collide with an id the app already uses?
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8790";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new", args: ["--no-sandbox","--disable-gpu"] });
const p = await b.newPage();
const csp = [];
p.on("console", m => { const t = m.text(); if (/Content Security Policy|Refused to/i.test(t)) csp.push(t); });
p.on("pageerror", e => csp.push("pageerror: " + e.message));
await p.setViewport({ width: 1400, height: 900 });
await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30_000 });
await new Promise(r => setTimeout(r, 2500));

const r = await p.evaluate(() => {
  const bot = document.querySelector(".tina4-bot");
  const svg = bot?.querySelector("svg");
  const ids = svg ? [...svg.querySelectorAll("[id]")].map(e => e.id).concat(svg.id ? [svg.id] : []) : [];
  // Every id in the document that is NOT inside the bot — a collision is an id in both sets.
  const outside = [...document.querySelectorAll("[id]")].filter(e => !bot?.contains(e)).map(e => e.id);
  const collisions = ids.filter(i => outside.includes(i));
  const hidden = document.getElementById("emjSaVDW3zs2");
  // Is the SVG's own stylesheet live in the main document?
  const sheets = [...document.styleSheets].filter(s => { try { return [...s.cssRules].some(r => r.selectorText === "#emjSaVDW3zs2"); } catch { return false; } });
  return {
    svgPresent: !!svg,
    idCount: ids.length,
    collisions,
    styleTagInDom: !!bot?.querySelector("style"),
    ruleActive: sheets.length > 0,
    hiddenElDisplay: hidden ? getComputedStyle(hidden).display : "(no #emjSaVDW3zs2 in document)",
    blendModes: svg ? [...svg.querySelectorAll("*")].filter(e => getComputedStyle(e).mixBlendMode === "multiply").length : 0,
  };
});
console.log(JSON.stringify(r, null, 2));
console.log("CSP / page errors:", csp.length ? csp : "(none)");
await b.close();
