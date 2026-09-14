// ui-05 slice 3: the remaining 33 native alert/confirm/prompt boxes.
//
// Drives the real UI in headless Chromium and asserts, per flow, that NO native dialog is raised
// and the app's own modal is what appears. Two independent detectors, because either alone can
// lie: puppeteer's `dialog` event (which also has to dismiss the box, or the page wedges), and a
// tripwire installed before any app script runs that records every call to window.alert/confirm/
// prompt. The tripwire is the one that matters -- it catches a call even if nothing is displayed.
//
//   npx tsx gate-ui.mjs <tree> [port]
//
// Run it against the SHIPPED tree to see it fail, and against the fixed tree to see it pass.
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const TREE = path.resolve(process.argv[2] || process.cwd());
// Resolved from the TREE under test, not from this file: the probe lives outside the repo and
// deliberately has no node_modules of its own.
const puppeteer = createRequire(path.join(TREE, "package.json"))("puppeteer-core");
const PORT = Number(process.argv[3] || 8933);
const CHROME = process.env.CHROME || "/usr/bin/chromium-browser";
const CAP_MS = 20_000;

const BOX = await fs.mkdtemp(path.join(os.tmpdir(), "ui05-"));
const HOME = path.join(BOX, "home");
await fs.mkdir(HOME, { recursive: true });

const results = [];
const check = (name, ok, detail = "") => { results.push({ name, ok: !!ok, detail }); console.log(`${ok ? "✅" : "❌"} ${name}${ok ? "" : "  — " + detail}`); };

// A stale server on this port makes every check below read the OLD code as a fresh success --
// the exact trap CLAUDE.md names. Refuse to start rather than report a result from someone else's
// process.
if (await fetch(`http://127.0.0.1:${PORT}/api/model`).then(() => true).catch(() => false)) {
  console.log(`VERDICT: CANNOT RUN -- something is already listening on ${PORT}. Kill it first.`);
  process.exit(2);
}

const app = spawn("setsid", ["npx", "tsx", "app.ts"], {
  cwd: TREE,
  env: { ...process.env,
    HOME, USERPROFILE: HOME,
    TINA4_STATE_DIR: path.join(BOX, "state"),
    TINA4_PROJECTS_ROOT: path.join(BOX, "projects"),
    TINA4_HOST: "127.0.0.1", TINA4_AGENT_PORT: String(PORT),
    TINA4_NO_BROWSER: "1", TINA4_DEBUG: "false" },
  stdio: ["ignore", "ignore", "pipe"], detached: true,
});
let stderr = ""; app.stderr.on("data", (d) => (stderr += String(d)));
// Killing the process GROUP, then reading the port back: npx spawns a child, and killing only the
// wrapper leaves the real server holding the port for the next run to mistake for its own.
const kill = async () => {
  try { process.kill(-app.pid, "SIGKILL"); } catch {}
  try { process.kill(app.pid, "SIGKILL"); } catch {}
  for (let i = 0; i < 15; i++) {
    if (!(await fetch(`${base}/api/model`).then(() => true).catch(() => false))) return true;
    await new Promise((r) => setTimeout(r, 200));
  }
  // Still up. `npx -> tsx -> node` puts the real server two levels down and it does not always
  // land in the group we signalled, so go by the PORT: whoever holds it is the thing to kill.
  const { execSync } = await import("node:child_process");
  try {
    const out = execSync(`ss -ltnp 2>/dev/null | grep ':${PORT} ' || true`, { encoding: "utf8" });
    for (const m of out.matchAll(/pid=(\d+)/g)) { try { process.kill(Number(m[1]), "SIGKILL"); } catch {} }
  } catch {}
  for (let i = 0; i < 15; i++) {
    if (!(await fetch(`${base}/api/model`).then(() => true).catch(() => false))) return true;
    await new Promise((r) => setTimeout(r, 200));
  }
  console.log(`WARNING: port ${PORT} is still answering after the kill -- a server leaked.`);
  return false;
};

const base = `http://127.0.0.1:${PORT}`;
const deadline = Date.now() + 60_000;
let up = false;
while (Date.now() < deadline && !up) {
  up = await fetch(`${base}/api/model`).then((r) => r.ok).catch(() => false);
  if (!up) await new Promise((r) => setTimeout(r, 400));
}
if (!up) { console.log(`VERDICT: CANNOT RUN — app did not start on ${PORT}. stderr: ${stderr.slice(-400)}`); await kill(); process.exit(2); }

// Seed through the API: a project to be in, and one session to act on. The ASSERTIONS are all on
// the UI; this is only setup, so that a flow is reachable at all.
await fetch(`${base}/api/projects`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ action: "new", name: "probe" }) });
const seeded = await fetch(`${base}/api/sessions`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ title: "seeded session" }) }).then((r) => r.json());
// A global secret, so Settings has a delete button — the one confirm that is raised from INSIDE
// another modal, which is what the stacking cell needs.
await fetch(`${base}/api/global-secrets`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "PROBE_SECRET", value: "not-a-real-key" }) });

// Two oversize text files for the queue cell: the attach loop calls notify() once per file, so
// two of them raise two notices before either is answered.
const bigA = path.join(BOX, "too-big-a.txt");
const bigB = path.join(BOX, "too-big-b.txt");
await fs.writeFile(bigA, "a".repeat(300 * 1024));
await fs.writeFile(bigB, "b".repeat(300 * 1024));

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--no-sandbox", "--disable-dev-shm-usage"] });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900 });

const native = [];   // what puppeteer saw
page.on("dialog", async (d) => { native.push({ type: d.type(), message: d.message() }); await d.dismiss().catch(() => {}); });
// The tripwire, installed before any page script: records the call itself, displayed or not.
await page.evaluateOnNewDocument(() => {
  window.__native = [];
  for (const k of ["alert", "confirm", "prompt"]) {
    const orig = window[k].bind(window);
    window[k] = (...a) => { window.__native.push({ kind: k, message: String(a[0] ?? "") }); return orig(...a); };
  }
});

const trip = () => page.evaluate(() => window.__native.slice());
const dialogText = () => page.$eval(".modal.dialog", (el) => el.innerText).catch(() => "");
const visible = (sel) => page.$(sel).then((h) => !!h);
const clickText = async (sel, text) => {
  const handles = await page.$$(sel);
  for (const h of handles) {
    const t = (await h.evaluate((el) => el.innerText || el.title || "")).trim();
    if (t === text || t.includes(text)) { await h.click(); return true; }
  }
  return false;
};
const settle = (ms = 350) => new Promise((r) => setTimeout(r, ms));

try {
  await page.goto(`${base}/`, { waitUntil: "domcontentloaded", timeout: CAP_MS });
  await settle(1500);

  // --- 1. rename a session: used to be prompt("Rename session", title)
  await page.$$eval(".rail-x", (els) => els.length).catch(() => 0);
  const railOpen = await visible(".rail-x");
  if (!railOpen) { await clickText("button", "sessions").catch(() => {}); await settle(600); }
  const renamed = await clickText('button[title="Rename"]', "");
  await settle(400);
  const sawRenameDialog = await visible(".modal.dialog");
  check("rename raises the app's dialog, not the browser's",
    renamed && sawRenameDialog && (await trip()).length === 0,
    `clicked=${renamed} styled=${sawRenameDialog} native=${JSON.stringify(await trip())}`);
  check("the rename dialog takes focus",
    await page.evaluate(() => document.activeElement && document.activeElement.id === "dialog-input"),
    await page.evaluate(() => document.activeElement && (document.activeElement.id || document.activeElement.tagName)));
  check("the rename dialog is seeded with the current title",
    (await page.$eval("#dialog-input", (el) => el.value).catch(() => "")) === "seeded session",
    await page.$eval("#dialog-input", (el) => el.value).catch(() => "<no input>"));

  // typing + Enter must actually rename it, server-side
  // Guarded, not assumed: on the shipped tree there is no input to type into, and the probe must
  // go on to report the OTHER flows rather than dying on the first one.
  if (await visible("#dialog-input")) {
    await page.$eval("#dialog-input", (el) => { el.value = ""; });
    await page.type("#dialog-input", "renamed by probe");
    await page.keyboard.press("Enter");
  } else {
    await page.keyboard.press("Escape");
  }
  await settle(700);
  const after = await fetch(`${base}/api/sessions`).then((r) => r.json()).catch(() => ({}));
  const list = after.sessions || after || [];
  check("Enter in the dialog renames the session on the server",
    JSON.stringify(list).includes("renamed by probe"), JSON.stringify(list).slice(0, 200));
  // Both halves, or this passes on a tree that never opened one (the same absence-pass that got
  // through in the w-20 attack suite).
  check("the dialog closes after it is answered", sawRenameDialog && !(await visible(".modal.dialog")), `opened=${sawRenameDialog}`);

  // --- 2. Escape cancels a prompt, and changes nothing
  await clickText('button[title="Rename"]', "");
  await settle(350);
  await page.keyboard.press("Escape");
  await settle(350);
  const stillNamed = await fetch(`${base}/api/sessions`).then((r) => r.json()).catch(() => ({}));
  check("Escape closes it and renames nothing",
    !(await visible(".modal.dialog")) && JSON.stringify(stillNamed).includes("renamed by probe"),
    "dialog still open or the title changed");

  // --- 3. delete a session: used to be confirm("Delete '...'?")
  await clickText('button[title="Delete"]', "");
  await settle(400);
  const delText = await dialogText();
  check("delete raises the app's dialog", (await visible(".modal.dialog")) && /Delete/.test(delText), delText.slice(0, 120));
  await clickText(".modal.dialog .btn.ghost", "Cancel");
  await settle(500);
  const afterCancel = await fetch(`${base}/api/sessions`).then((r) => r.json()).catch(() => ({}));
  check("Cancel on the delete dialog keeps the session",
    JSON.stringify(afterCancel).includes(seeded.id), `seeded id ${seeded.id} gone: ` + JSON.stringify(afterCancel).slice(0, 200));

  await clickText('button[title="Delete"]', "");
  await settle(400);
  const sawDeleteDialog = await visible(".modal.dialog");
  await clickText(".modal.dialog .btn.danger", "Delete");
  await settle(800);
  const afterDelete = await fetch(`${base}/api/sessions`).then((r) => r.json()).catch(() => ({}));
  // By ID, not by the renamed title: on a tree where the rename never happened, a title check
  // would pass because the string was never there in the first place.
  check("confirming the delete dialog deletes the session",
    sawDeleteDialog && !JSON.stringify(afterDelete).includes(seeded.id), `styled=${sawDeleteDialog} list=` + JSON.stringify(afterDelete).slice(0, 160));

  // --- 4. the one dialog every user meets last: Quit
  const gear = await clickText("button", "⚙") || await clickText('button[title*="Settings"]', "");
  await settle(600);
  const quitClicked = await clickText(".modal-actions .btn.danger", "Quit");
  await settle(400);
  const quitText = await dialogText();
  check("Quit asks in the app's dialog", quitClicked && /Quit Tina4 Agent/.test(quitText), `clicked=${quitClicked} text=${quitText.slice(0, 120)}`);
  await clickText(".modal.dialog .btn.ghost", "Cancel");
  await settle(300);
  check("cancelling Quit leaves the app running", await fetch(`${base}/api/model`).then((r) => r.ok).catch(() => false));

  // --- 5. a dialog raised from INSIDE a modal must paint above it
  // (Settings is still open — Quit was cancelled, not confirmed.)
  const secretDeleted = await clickText(".modal .btn.tiny.danger", "delete");
  await settle(400);
  const stack = await page.evaluate(() => {
    const d = document.querySelector(".dialog-backdrop");
    if (!d) return null;
    const r = d.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return {
      dialogZ: Number(getComputedStyle(d).zIndex),
      otherZ: Math.max(...[...document.querySelectorAll(".modal-backdrop:not(.dialog-backdrop)")].map((e) => Number(getComputedStyle(e).zIndex) || 0), 0),
      topmostIsDialog: !!top && !!top.closest(".modal.dialog"),
    };
  });
  check("a dialog raised from inside Settings paints above it",
    secretDeleted && stack && stack.dialogZ > stack.otherZ && stack.topmostIsDialog, `clicked=${secretDeleted} ${JSON.stringify(stack)}`);
  // Escape must settle the DIALOG and leave Settings open. Every modal listens for Escape on
  // window, and they registered first, so a bubble-phase handler here would close Settings
  // underneath the confirm the user is answering.
  await page.keyboard.press("Escape");
  await settle(400);
  check("Escape closes the dialog only, not the modal underneath it",
    !(await visible(".modal.dialog")) && (await visible(".modal-backdrop")),
    `dialog=${await visible(".modal.dialog")} settings=${await visible(".modal-backdrop")}`);
  const secretsLeft = await fetch(`${base}/api/global-secrets`).then((r) => r.json()).catch(() => ({}));
  check("cancelling that dialog keeps the secret", JSON.stringify(secretsLeft).includes("PROBE_SECRET"), JSON.stringify(secretsLeft).slice(0, 160));

  // --- 6. two notices raised before either is answered: the queue, not a last-one-wins slot.
  // alert() blocked, so the pair used to be shown one after the other. Losing the first silently
  // is the regression this cell exists for.
  await page.keyboard.press("Escape");                       // close Settings
  await settle(400);
  const fileInput = await page.$(".att-input");
  if (!fileInput) check("two oversize files raise two notices, in order", false, "no .att-input in the page");
  else {
    await fileInput.uploadFile(bigA, bigB);
    await settle(900);
    const first = await dialogText();
    await clickText(".modal.dialog .btn.primary", "OK");
    await settle(400);
    const second = await dialogText();
    await clickText(".modal.dialog .btn.primary", "OK");
    await settle(400);
    const gone = !(await visible(".modal.dialog"));
    check("two oversize files raise two notices, in order",
      /too large/i.test(first) && /too large/i.test(second) && gone,
      `first=${JSON.stringify(first.slice(0, 60))} second=${JSON.stringify(second.slice(0, 60))} closed=${gone}`);
  }

  // --- 7. the Link button: the one call site where making the ask asynchronous can break the
  // FEATURE rather than the look. execCommand("createLink") acts on the live selection, which the
  // old native prompt held only because it blocked. Nothing else in this slice has that property.
  await fetch(`${base}/api/file`, { method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ path: "notes.md", content: "# Notes\n\nlink me please\n" }) });
  const treeBtn = await page.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find((x) => (x.title || "").toLowerCase().includes("file"));
    if (b) { b.click(); return b.title; }
    return null;
  });
  await settle(900);
  const opened = await page.evaluate(() => {
    const row = [...document.querySelectorAll(".tree-row.file")].find((r) => r.innerText.includes("notes.md"));
    if (!row) return false;
    row.click(); return true;
  });
  await settle(1200);
  const toolbar = await visible(".md-toolbar");
  if (!toolbar) {
    const rows = await page.evaluate(() => [...document.querySelectorAll(".tree-row")].map((r) => r.className + "|" + r.innerText.trim()).slice(0, 20));
    check("Link inserts a link at the selection", false, `could not reach the markdown editor (treeBtn=${treeBtn} openedRow=${opened}) rows=${JSON.stringify(rows)}`);
  }
  else {
    // Select the words "link me" inside the editable body, exactly as a user would by dragging.
    const selected = await page.evaluate(() => {
      const body = document.querySelector(".wysiwyg");
      if (!body) return false;
      const walk = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
      let node; while ((node = walk.nextNode())) {
        const i = node.textContent.indexOf("link me");
        if (i >= 0) {
          const r = document.createRange();
          r.setStart(node, i); r.setEnd(node, i + "link me".length);
          const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
          return true;
        }
      }
      return false;
    });
    await page.evaluate(() => [...document.querySelectorAll(".md-toolbar button")].find((b) => b.title === "Link")?.dispatchEvent(new MouseEvent("mousedown", { bubbles: true })));
    await settle(500);
    const asked = await visible(".modal.dialog");
    if (asked) {
      await page.$eval("#dialog-input", (el) => { el.value = ""; });
      await page.type("#dialog-input", "https://example.test/x");
      await page.keyboard.press("Enter");
      await settle(600);
    }
    const href = await page.evaluate(() => document.querySelector('.wysiwyg a[href="https://example.test/x"]')?.textContent ?? null);
    check("Link inserts a link at the selection", selected && asked && href === "link me",
      `selected=${selected} asked=${asked} linkText=${JSON.stringify(href)}`);
  }

  // --- 8. both detectors, over everything above
  const tripped = await trip();
  check("no native dialog was called at any point", tripped.length === 0 && native.length === 0,
    `tripwire=${JSON.stringify(tripped)} puppeteer=${JSON.stringify(native)}`);
} catch (e) {
  check("the probe ran to the end", false, String(e.message).split("\n")[0]);
} finally {
  await browser.close().catch(() => {});
  await kill();
  await fs.rm(BOX, { recursive: true, force: true }).catch(() => {});
}

const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed}/${results.length} passed`);
console.log(failed ? "VERDICT: FAIL" : "VERDICT: PASS — every flow drives the app's own dialog and nothing calls the browser's.");
process.exit(failed ? 1 : 0);
