// The second user: closes it, submits nothing, mashes the button, types only a title.
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8796";
const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });

const fresh = async () => {
  const p = await b.newPage();
  p.on("dialog", async d => { console.error("   !! NATIVE DIALOG:", d.type(), d.message()); await d.dismiss(); });
  await p.setViewport({ width: 1600, height: 900 });
  await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
  await new Promise(r => setTimeout(r, 2200));
  await p.evaluate(() => { window.__native = []; ["alert","confirm","prompt"].forEach(k => { window[k] = (m) => { window.__native.push([k, String(m).slice(0,40)]); return k === "confirm" ? true : ""; }; }); });
  return p;
};
const count = (p) => p.evaluate(async () => { const j = await (await fetch("/api/sessions")).json(); const l = Array.isArray(j)?j:(j.sessions??[]); return l.length; });
const open  = (p) => p.evaluate(() => { [...document.querySelectorAll("button")].find(x => (x.textContent||"").trim().toLowerCase()==="new session")?.click(); });
const modalUp = (p) => p.evaluate(() => !!document.querySelector(".modal") && document.querySelector(".modal").getBoundingClientRect().width > 50);
const nat = (p) => p.evaluate(() => window.__native.length);

const cases = {
  "escape closes, creates nothing": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    await p.keyboard.press("Escape"); await new Promise(r=>setTimeout(r,700));
    return { modalGone: !(await modalUp(p)), created: (await count(p)) - n0 };
  },
  "backdrop click closes, creates nothing": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    await p.evaluate(() => { const bd = document.querySelector(".modal-backdrop"); bd.dispatchEvent(new MouseEvent("click", { bubbles: true })); });
    await new Promise(r=>setTimeout(r,700));
    return { modalGone: !(await modalUp(p)), created: (await count(p)) - n0 };
  },
  "empty title refuses (old behaviour)": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    await p.evaluate(() => [...document.querySelectorAll(".modal button")].find(x=>/create/i.test(x.textContent))?.click());
    await new Promise(r=>setTimeout(r,900));
    return { modalStillUp: await modalUp(p), created: (await count(p)) - n0 };
  },
  "title only, blanks allowed": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    const t = "attack-titleonly-" + Date.now();
    await p.evaluate((v) => { const i = document.querySelector("#ns-title"); i.value = v; i.dispatchEvent(new Event("input",{bubbles:true})); }, t);
    await p.evaluate(() => [...document.querySelectorAll(".modal button")].find(x=>/create/i.test(x.textContent))?.click());
    await new Promise(r=>setTimeout(r,1600));
    const got = await p.evaluate(async (t) => { const j=await(await fetch("/api/sessions")).json(); const l=Array.isArray(j)?j:(j.sessions??[]); const s=l.find(x=>x.title===t); return s ? { goal: s.goal, subpath: s.subpath } : null; }, t);
    return { created: (await count(p)) - n0, record: JSON.stringify(got), modalGone: !(await modalUp(p)) };
  },
  "Enter in title submits": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    await p.type("#ns-title", "attack-enter-" + Date.now());
    await p.keyboard.press("Enter"); await new Promise(r=>setTimeout(r,1600));
    return { created: (await count(p)) - n0, modalGone: !(await modalUp(p)) };
  },
  "double-click Create makes ONE": async (p) => {
    const n0 = await count(p); await open(p); await new Promise(r=>setTimeout(r,400));
    await p.type("#ns-title", "attack-double-" + Date.now());
    await p.evaluate(() => { const btn=[...document.querySelectorAll(".modal button")].find(x=>/create/i.test(x.textContent)); btn.click(); btn.click(); btn.click(); });
    await new Promise(r=>setTimeout(r,2200));
    return { created: (await count(p)) - n0 };
  },
  "other modals still open": async (p) => {
    const r = {};
    for (const [title, sel] of [["New project","new-project-modal"],["Settings","settings-modal"]]) {
      await p.evaluate((t) => [...document.querySelectorAll("button")].find(x=>(x.title||"").trim()===t)?.click(), title);
      await new Promise(x=>setTimeout(x,700));
      r[sel] = await p.evaluate((s) => !!document.querySelector(s) && !!document.querySelector(".modal"), sel);
      await p.keyboard.press("Escape"); await new Promise(x=>setTimeout(x,400));
    }
    return r;
  },
};

for (const [name, fn] of Object.entries(cases)) {
  const p = await fresh();
  let out; try { out = await fn(p); } catch (e) { out = { ERROR: String(e).slice(0,120) }; }
  const n = await nat(p);
  console.log(`  ${name.padEnd(34)} ${JSON.stringify(out)}  nativeDialogs=${n}`);
  await p.close();
}
await b.close();
