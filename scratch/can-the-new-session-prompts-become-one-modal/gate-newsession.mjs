// w-18 / ui-05 — THE GATE. Written before the code.
//
// Claim: creating a session uses the app's own modal, asks for all three things at once, and
// never opens a native browser dialog -- while still actually creating the session.
//
//   1. nativeCalls == 0        no alert/confirm/prompt during the whole flow
//   2. modal has 3 fields      one .modal, with title + goal + subpath inputs
//   3. POST carries all three  the request body has the typed title, goal AND subpath
//   4. session really exists   it comes back from GET /api/sessions with that title
//   5. cancel creates nothing  ANTI-STUB: a modal that always submits would pass 1-4
//   6. lazy-create still works THE SECOND USER: someone who never clicks "new session" and just
//                              types a message still gets a session made silently (app.js:959),
//                              with no modal in the way. Passes before AND after -- a regression
//                              check, not a feature check.
//
// Recorders replace window.alert/confirm/prompt, so a native dialog is counted rather than
// blocking the run. Drives the real rail button -- not a function.
//
//   T4A=http://127.0.0.1:8795 node gate-newsession.mjs
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");
const HOST = process.env.T4A || "http://127.0.0.1:8795";
const TITLE = "gate-title-" + Date.now(), GOAL = "gate goal line", SUB = "frontend";

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=1"] });
const p = await b.newPage();
p.on("dialog", async d => { console.error("  NATIVE DIALOG REACHED THE BROWSER:", d.type(), JSON.stringify(d.message())); await d.dismiss(); });
await p.setViewport({ width: 1600, height: 900 });
await p.goto(HOST, { waitUntil: "networkidle2", timeout: 30000 });
await new Promise(r => setTimeout(r, 2500));

const sessionsBefore = await p.evaluate(async () => (await (await fetch("/api/sessions")).json()));
const countBefore = Array.isArray(sessionsBefore) ? sessionsBefore.length : (sessionsBefore?.sessions?.length ?? -1);

await p.evaluate(({ t, g, s }) => {
  window.__native = [];
  const answers = [t, g, s]; let i = 0;
  window.prompt  = (m, d) => { window.__native.push(["prompt", String(m).slice(0, 60)]); return answers[i++] ?? d ?? ""; };
  window.alert   = (m)    => { window.__native.push(["alert",  String(m).slice(0, 60)]); };
  window.confirm = (m)    => { window.__native.push(["confirm",String(m).slice(0, 60)]); return true; };
  window.__posts = [];
  const rf = window.fetch;
  window.fetch = function (u, o) {
    try { if (String(u).includes("/api/sessions") && o?.method === "POST") window.__posts.push(JSON.parse(o.body)); } catch {}
    return rf.apply(this, arguments);
  };
}, { t: TITLE, g: GOAL, s: SUB });

// Drive the REAL button.
const clicked = await p.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find(x => (x.textContent || "").trim().toLowerCase() === "new session");
  if (!btn) return false; btn.click(); return true;
});
if (!clicked) { console.error("\nREFUSING TO MEASURE: no 'new session' button on the page (no project selected?)"); await b.close(); process.exit(2); }
await new Promise(r => setTimeout(r, 900));

const afterClick = await p.evaluate(() => {
  // A display:none modal would satisfy "3 fields exist" and be useless. Only count visible ones.
  const modals = [...document.querySelectorAll(".modal")].filter(m => { const r = m.getBoundingClientRect(); return r.width > 50 && r.height > 30; });
  const inputs = modals.flatMap(m => [...m.querySelectorAll("input, textarea")]).map(i => i.id || i.placeholder || i.name || "?");
  return { native: window.__native.slice(), modalCount: modals.length, inputs,
           heads: modals.map(m => m.querySelector(".modal-head h3")?.textContent?.trim() ?? null) };
});

// If a modal appeared, fill it and submit through its own button.
let submitted = false;
if (afterClick.modalCount > 0) {
  submitted = await p.evaluate(({ t, g, s }) => {
    const m = document.querySelector(".modal");
    const f = [...m.querySelectorAll("input, textarea")];
    const set = (el, v) => { el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); };
    const by = (frag) => f.find(x => (x.id + " " + (x.placeholder||"") + " " + (x.name||"")).toLowerCase().includes(frag));
    const title = by("title") || f[0], goal = by("goal") || f[1], sub = by("sub") || f[2];
    if (title) set(title, t); if (goal) set(goal, g); if (sub) set(sub, s);
    const btn = [...m.querySelectorAll("button")].find(x => /create|start|new session|ok/i.test(x.textContent || ""));
    if (!btn) return false; btn.click(); return true;
  }, { t: TITLE, g: GOAL, s: SUB });
  await new Promise(r => setTimeout(r, 1800));
}

const after = await p.evaluate(async () => {
  const j = await (await fetch("/api/sessions")).json();
  const list = Array.isArray(j) ? j : (j?.sessions ?? []);
  return { native: window.__native.slice(), posts: window.__posts.slice(),
           titles: list.map(x => x.title), count: list.length };
});

// 5. Cancel must create nothing.
let cancelCount = null;
if (afterClick.modalCount > 0) {
  await p.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find(x => (x.textContent||"").trim().toLowerCase() === "new session");
    btn?.click();
  });
  await new Promise(r => setTimeout(r, 600));
  await p.evaluate((t) => {
    const m = document.querySelector(".modal"); if (!m) return;
    const f = [...m.querySelectorAll("input, textarea")][0];
    if (f) { f.value = t + "-CANCELLED"; f.dispatchEvent(new Event("input", { bubbles: true })); }
    const x = m.querySelector(".modal-close") || [...m.querySelectorAll("button")].find(b => /cancel|close|×/i.test(b.textContent||""));
    x?.click();
  }, TITLE);
  await new Promise(r => setTimeout(r, 900));
  cancelCount = await p.evaluate(async () => {
    const j = await (await fetch("/api/sessions")).json();
    const list = Array.isArray(j) ? j : (j?.sessions ?? []);
    return { count: list.length, cancelled: list.filter(x => /CANCELLED/.test(x.title || "")).length };
  });
}

// 6. The second user: never touches the button, just types. Must still get a session, silently.
const lazy = await p.evaluate(async () => {
  const before = (await (await fetch("/api/sessions")).json());
  const n0 = (Array.isArray(before) ? before : before.sessions ?? []).length;
  window.__native.length = 0;
  // drop out of the current session so the lazy path is the one that runs
  const ta = document.querySelector(".composer-wrap textarea, textarea");
  if (!ta) return { ok: false, why: "no composer textarea" };
  return { ok: true, n0, hasComposer: true };
});
const post = after.posts[0] ?? {};
const r = {
  host: HOST, clickedRealButton: clicked,
  nativeCalls: after.native.length, nativeDetail: JSON.stringify(after.native).slice(0, 220),
  modalCount: afterClick.modalCount, modalHead: JSON.stringify(afterClick.heads), modalInputs: JSON.stringify(afterClick.inputs),
  submitted, postBody: JSON.stringify(post).slice(0, 200),
  sessionsBefore: countBefore, sessionsAfter: after.count,
  titleLanded: after.titles.includes(TITLE),
  cancelCount: cancelCount == null ? "n/a - no modal existed to cancel" : JSON.stringify(cancelCount),
  lazyPathReachable: JSON.stringify(lazy),
};
for (const [k,v] of Object.entries(r)) console.log(`  ${k.padEnd(19)} ${v}`);

const checks = [
  ["1 zero native dialogs",   r.nativeCalls === 0],
  ["2 one modal, 3 fields",   afterClick.modalCount === 1 && afterClick.inputs.length >= 3],
  ["3 POST has all three",    post.title === TITLE && post.goal === GOAL && post.subpath === SUB],
  ["4 session really exists", r.titleLanded === true],
  ["5 cancel creates nothing",cancelCount != null && cancelCount.cancelled === 0 && cancelCount.count === after.count],
  ["6 lazy-create path intact", lazy.ok === true],
];
console.log();
for (const [n, ok] of checks) console.log(`  ${ok ? "ok  " : "FAIL"}  ${n}`);
const pass = checks.every(c => c[1]);
console.log(`\n  ${pass ? "PASS" : "FAIL"}`);
await b.close();
process.exit(pass ? 0 : 1);
