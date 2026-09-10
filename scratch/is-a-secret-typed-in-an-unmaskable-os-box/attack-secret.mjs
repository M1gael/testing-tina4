// ui-05 slice 2 -- ATTACK. The gate drives the PROJECT list only, through one happy path. These are
// the cells it does not visit: the GLOBAL list (the second call site), the ways a user leaves a
// dialog without saving, an empty value, Enter-to-submit, and two secrets in a row -- where a signal
// reused across rows could show or overwrite the wrong name.
//
//   T4A=http://127.0.0.1:8796 SECRETS_DIR=... GLOBAL_DIR=... node attack-secret.mjs
import { createRequire } from "node:module";
import { promises as fs } from "node:fs";
import path from "node:path";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");

const HOST = process.env.T4A || "http://127.0.0.1:8796";
const PROJ = process.env.SECRETS_DIR, GLOB = process.env.GLOBAL_DIR;
if (!PROJ || !GLOB) { console.error("SECRETS_DIR and GLOBAL_DIR are required"); process.exit(2); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rd = (dir, n) => fs.readFile(path.join(dir, n), "utf8").catch(() => "(absent)");

const A = "ATK_ONE", B = "ATK_TWO", G = "ATK_GLOBAL";
await fs.mkdir(PROJ, { recursive: true }); await fs.mkdir(GLOB, { recursive: true });
await fs.writeFile(path.join(PROJ, A), "A-original", { mode: 0o600 });
await fs.writeFile(path.join(PROJ, B), "B-original", { mode: 0o600 });
await fs.writeFile(path.join(GLOB, G), "G-original", { mode: 0o600 });

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"] });
const p = await b.newPage();
p.on("dialog", async (d) => { console.error("  NATIVE DIALOG:", d.type(), d.message()); await d.dismiss(); });
await p.setViewport({ width: 1400, height: 950 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await p.evaluate(() => { window.__native = []; window.prompt = (m) => { window.__native.push(["prompt", String(m)]); return "X"; };
  window.confirm = (m) => { window.__native.push(["confirm", String(m)]); return true; }; window.alert = (m) => { window.__native.push(["alert", String(m)]); }; });

const results = [];
const check = (n, ok, d = "") => { results.push({ n, ok }); console.log(`  ${ok ? "ok  " : "FAIL"} ${n}${ok ? "" : "  -- " + d}`); };
const dlgOpen = () => p.$$eval("#secret-value", (x) => x.length === 1).catch(() => false);
const headText = () => p.$eval("#secret-value", (e) => e.closest(".modal")?.querySelector(".modal-head h3")?.textContent.trim() || "").catch(() => "");
const openProject = async () => { if (!(await p.$('.secret-row'))) { await p.click('button.cog-btn[title="Edit current project"]'); await sleep(900); } };
const openSettings = async () => { await p.click('button.cog-btn[title="Settings"]'); await sleep(1100); };
const clickRow = (name, which) => p.evaluate((n, w) => {
  const row = [...document.querySelectorAll(".secret-row")].find((r) => r.querySelector(".secret-name")?.textContent.trim() === n);
  const btn = [...(row?.querySelectorAll("button") || [])].find((x) => new RegExp(w, "i").test(x.textContent));
  if (!btn) return false; btn.click(); return true;
}, name, which);
const typeIn = async (v) => { const f = await p.$("#secret-value"); if (!f) return false; await f.click(); if (v) await f.type(v); return true; };
const clickDlg = (re) => p.evaluate((r) => {
  const dlg = document.querySelector("#secret-value")?.closest(".modal");
  [...(dlg?.querySelectorAll(".modal-actions button, .modal-close") || [])].find((x) => new RegExp(r, "i").test(x.textContent))?.click();
}, re);

try {
  // --- cell 1: the field never arrives pre-filled. A pre-filled value would put the old secret back
  //     on screen, which is the exact thing this change exists to stop.
  await openProject();
  await clickRow(A, "replace"); await sleep(500);
  const initial = await p.$eval("#secret-value", (e) => e.value).catch(() => "(no field)");
  check("field opens EMPTY, never pre-filled with the old value", initial === "", JSON.stringify(initial));

  // --- cell 2: Escape closes and writes nothing.
  await typeIn("escape-should-discard");
  await p.keyboard.press("Escape"); await sleep(500);
  check("Escape closes and writes nothing", !(await dlgOpen()) && (await rd(PROJ, A)) === "A-original", await rd(PROJ, A));

  // --- cell 3: clicking the backdrop closes and writes nothing.
  await openProject(); await clickRow(A, "replace"); await sleep(500);
  await typeIn("backdrop-should-discard");
  await p.evaluate(() => { const d = document.querySelector("#secret-value")?.closest(".modal-backdrop");
    d?.dispatchEvent(new MouseEvent("click", { bubbles: true })); });
  await sleep(500);
  check("backdrop click closes and writes nothing", !(await dlgOpen()) && (await rd(PROJ, A)) === "A-original", await rd(PROJ, A));

  // --- cell 4: an EMPTY value must do nothing and leave the dialog open (the old rule was
  //     `if (v && v.length)` -- a blank prompt saved nothing, and that must not have changed).
  await openProject(); await clickRow(A, "replace"); await sleep(500);
  await typeIn("");
  await clickDlg("replace"); await sleep(700);
  check("empty value writes nothing and keeps the dialog open", (await dlgOpen()) && (await rd(PROJ, A)) === "A-original", await rd(PROJ, A));
  await p.keyboard.press("Escape"); await sleep(400);

  // --- cell 5: Enter submits from the field.
  await openProject(); await clickRow(A, "replace"); await sleep(500);
  await typeIn("via-enter-key");
  await p.keyboard.press("Enter"); await sleep(1200);
  check("Enter submits", (await rd(PROJ, A)) === "via-enter-key" && !(await dlgOpen()), await rd(PROJ, A));

  // --- cell 6: a SECOND row must ask for, and write, ITS OWN name -- not the previous one's.
  await openProject(); await clickRow(B, "replace"); await sleep(500);
  const head = await headText();
  await typeIn("B-replaced"); await clickDlg("replace"); await sleep(1200);
  check("second row names and writes ITSELF, not the previous row",
    head.includes(B) && (await rd(PROJ, B)) === "B-replaced" && (await rd(PROJ, A)) === "via-enter-key",
    `head=${JSON.stringify(head)} A=${await rd(PROJ, A)} B=${await rd(PROJ, B)}`);

  // --- cell 7: THE OTHER CALL SITE. Global secrets, in Settings -- never touched by the gate.
  await p.evaluate(() => document.querySelectorAll(".modal-close").forEach((x) => x.click()));
  await sleep(400);
  await openSettings();
  const gRows = await p.$$eval(".secret-row .secret-name", (n) => n.map((e) => e.textContent.trim())).catch(() => []);
  await clickRow(G, "replace"); await sleep(600);
  const gHead = await headText();
  const gOpened = await dlgOpen();
  const gMasked = await p.$eval("#secret-value", (e) => e.getAttribute("type")).catch(() => null);
  if (gOpened) { await typeIn("G-replaced"); await clickDlg("replace"); await sleep(1400); }
  check("global secrets use the same masked dialog and save to the GLOBAL dir",
    gOpened && gMasked === "password" && gHead.includes(G) && (await rd(GLOB, G)) === "G-replaced",
    `rows=${JSON.stringify(gRows)} opened=${gOpened} masked=${gMasked} head=${JSON.stringify(gHead)} disk=${await rd(GLOB, G)}`);

  // --- cell 8: a global replace must not have touched the project-scoped file of any name.
  check("replacing a global secret leaves project secrets alone",
    (await rd(PROJ, A)) === "via-enter-key" && (await rd(PROJ, B)) === "B-replaced",
    `A=${await rd(PROJ, A)} B=${await rd(PROJ, B)}`);

  // --- cell 9: no native prompt anywhere in any of that.
  const nat = await p.evaluate(() => window.__native.slice());
  check("no native prompt in any replace path", nat.filter(([k]) => k === "prompt").length === 0, JSON.stringify(nat));
} catch (e) { check("probe ran to completion", false, String(e).slice(0, 200)); }
finally { await b.close(); }

console.log("");
const bad = results.filter((r) => !r.ok).length;
console.log(bad ? `  ${bad} of ${results.length} FAILED` : `  all ${results.length} clean`);
process.exit(bad ? 1 : 0);
