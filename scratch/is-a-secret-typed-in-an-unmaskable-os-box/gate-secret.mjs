// ui-05 slice 2 -- THE GATE. Written before the code, then rewritten because the first draft was
// measuring the wrong things: three of its six checks passed on the UNTOUCHED tree. `.modal` matched
// the PROJECT modal that was already open, and `input[type=password]` matched the ADD-secret field
// that has always been masked -- so "a masked input exists in a modal" was true before the feature
// did. And two checks were vacuous: nothing had been typed, so "the value never renders" could not
// fail, and "cancel wrote nothing" compared a value to itself.
//
// This version pins the replace dialog to an element that does not exist today (#secret-value),
// asserts each phase's PRECONDITION before its result, and fails -- rather than passes -- when a
// step could not be performed.
//
// Claim: replacing a stored secret asks for the new value INSIDE the app, in a masked field, and
// never in a native browser box, while still actually writing the secret.
//
//   T4A=http://127.0.0.1:8796 SECRETS_DIR=/tmp/.../.secrets node gate-secret.mjs
import { createRequire } from "node:module";
import { promises as fs } from "node:fs";
import path from "node:path";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");

const HOST = process.env.T4A || "http://127.0.0.1:8796";
const SECRETS = process.env.SECRETS_DIR;
if (!SECRETS) { console.error("SECRETS_DIR is required"); process.exit(2); }
const NAME = "GATE_KEY", OLD = "old-value-0000", CANCELLED = "typed-then-cancelled-" + Date.now(), NEW = "s3cr3t-" + Date.now();
const file = path.join(SECRETS, NAME);
const read = async () => fs.readFile(file, "utf8").catch(() => "(absent)");
const mode = async () => fs.stat(file).then((s) => (s.mode & 0o777).toString(8)).catch(() => "?");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

await fs.mkdir(SECRETS, { recursive: true });
await fs.writeFile(file, OLD, { mode: 0o600 });

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"] });
const p = await b.newPage();
p.on("dialog", async (d) => { console.error("  NATIVE DIALOG REACHED THE BROWSER:", d.type(), JSON.stringify(d.message())); await d.dismiss(); });
await p.setViewport({ width: 1400, height: 900 });

// The replace dialog is identified by #secret-value -- an element that does NOT exist on the
// untouched tree, so nothing here can be satisfied by the project modal or the add-secret field.
const dialogOpen = () => p.$$eval("#secret-value", (n) => n.length === 1).catch(() => false);
const openProjectModal = async () => { await p.click('button.cog-btn[title="Edit current project"]'); await sleep(900); };
const clickRow = (name, which) => p.evaluate((n, w) => {
  const row = [...document.querySelectorAll(".secret-row")].find((r) => r.querySelector(".secret-name")?.textContent.trim() === n);
  const btn = [...(row?.querySelectorAll("button") || [])].find((x) => new RegExp(w, "i").test(x.textContent));
  if (!btn) return false; btn.click(); return true;
}, name, which);

const out = {};
try {
  await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
  await p.evaluate(() => {
    window.__native = [];
    window.prompt = (m, d) => { window.__native.push(["prompt", String(m)]); return d ?? "RECORDER-RETURNED-THIS"; };
    window.alert = (m) => { window.__native.push(["alert", String(m)]); };
    window.confirm = (m) => { window.__native.push(["confirm", String(m)]); return true; };
  });

  await openProjectModal();
  out.rowsVisible = await p.$$eval(".secret-row .secret-name", (n) => n.map((e) => e.textContent.trim()));
  out.projectModalWasAlreadyOpen = await p.$$eval(".modal", (n) => n.length);   // context, not a check

  // ---- phase A: cancel. Precondition: the dialog opened AND we typed into it.
  out.clickedReplaceA = await clickRow(NAME, "replace");
  await sleep(600);
  out.dialogOpenedA = await dialogOpen();
  out.maskedA = await p.$$eval("#secret-value", (n) => n.map((e) => e.getAttribute("type")));
  if (out.dialogOpenedA) {
    const f = await p.$("#secret-value"); await f.click(); await f.type(CANCELLED);
    out.typedA = await p.$eval("#secret-value", (e) => e.value.length) > 0;
    // ANTI-EXPOSURE, measured with a real value sitting in the field.
    out.exposure = await p.evaluate((v) => ({
      inBodyText: document.body.innerText.includes(v),
      inValueAttribute: [...document.querySelectorAll("[value]")].some((e) => e.getAttribute("value")?.includes(v)),
      inOuterHTML: document.body.outerHTML.includes(v),
    }), CANCELLED);
    const before = await read();
    await p.evaluate(() => {
      const dlg = document.querySelector("#secret-value")?.closest(".modal");
      [...(dlg?.querySelectorAll(".modal-actions button, .modal-close") || [])].find((x) => /cancel/i.test(x.textContent))?.click();
    });
    await sleep(600);
    out.dialogClosedA = !(await dialogOpen());
    out.cancelWroteNothing = (await read()) === before && before === OLD;
  } else { out.typedA = false; out.exposure = null; out.dialogClosedA = false; out.cancelWroteNothing = false; }

  // ---- phase B: save for real. Precondition: dialog opened again and accepted a value.
  if (!(await p.$(".secret-row"))) await openProjectModal();
  out.clickedReplaceB = await clickRow(NAME, "replace");
  await sleep(600);
  out.dialogOpenedB = await dialogOpen();
  if (out.dialogOpenedB) {
    const f = await p.$("#secret-value"); await f.click(); await f.type(NEW);
    await p.evaluate(() => {
      const dlg = document.querySelector("#secret-value")?.closest(".modal");
      [...(dlg?.querySelectorAll(".modal-actions button") || [])].find((x) => !/cancel/i.test(x.textContent))?.click();
    });
    await sleep(1400);
  }
  out.onDisk = await read();
  out.diskMode = await mode();
  out.dialogClosedB = !(await dialogOpen());

  // ---- phase C: the neighbouring delete button still works. Precondition: the row is there.
  if (!(await p.$(".secret-row"))) await openProjectModal();
  out.rowStillThere = await p.$$eval(".secret-row .secret-name", (n) => n.map((e) => e.textContent.trim()));
  out.clickedDelete = await clickRow(NAME, "delete");
  await sleep(1000);
  out.deletedFromDisk = (await read()) === "(absent)";

  out.nativeTotal = await p.evaluate(() => window.__native.slice());
  // Check 1 is scoped to the REPLACE flow -- the delete button's confirm() is on the same row but is
  // not this slice's evidence (it leaks nothing) and belongs to the bulk dialog sweep. Counted and
  // reported separately so the scope is visible rather than quietly assumed.
  out.nativeDuringReplace = (out.nativeTotal || []).filter(([kind]) => kind === "prompt");
  out.nativeLeftOnThisRow = (out.nativeTotal || []).filter(([kind]) => kind !== "prompt");
} catch (e) { out.error = String(e).slice(0, 220); }
finally { await b.close(); }

for (const [k, v] of Object.entries(out)) console.log("  " + k.padEnd(24), JSON.stringify(v));
console.log("");
const checks = [
  ["1 zero native prompts in the replace flow", Array.isArray(out.nativeDuringReplace) && out.nativeDuringReplace.length === 0],
  ["2 replace opens an in-app dialog with a MASKED field", out.dialogOpenedA === true && JSON.stringify(out.maskedA) === '["password"]'],
  ["3 the typed value renders nowhere", out.typedA === true && out.exposure && !out.exposure.inBodyText && !out.exposure.inValueAttribute && !out.exposure.inOuterHTML],
  ["4 saving writes the new value, still 0600", out.onDisk === NEW && out.diskMode === "600"],
  ["5 cancel writes nothing and closes (anti-stub)", out.cancelWroteNothing === true && out.dialogClosedA === true],
  ["6 delete on the same row still works", out.clickedDelete === true && out.deletedFromDisk === true],
];
let bad = 0;
for (const [n, ok] of checks) { console.log(`  ${ok ? "ok  " : "FAIL"} ${n}`); if (!ok) bad++; }
console.log("");
console.log(bad ? `  FAIL -- ${bad} of ${checks.length}` : "  PASS");
process.exit(bad ? 1 : 0);
