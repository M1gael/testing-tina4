// Is the "typed text got appended to the seeded value" result a PROBE artefact or a real defect?
//
// gate-ui.mjs's first run read back "https://mcp.tina4.com/v1http://127.0.0.1:8901/v1" -- the new
// text concatenated onto the pre-filled one. That is either (a) puppeteer's triple-click failing to
// select inside an input whose value comes from a property binding, or (b) a field a real person
// cannot edit. Those have opposite consequences, so it gets measured rather than assumed.
//
// Three gestures, NONE of which clear the field programmatically -- every one is something a person
// physically does:
//   ctrlA      click, Control+A, type
//   backspace  click, End, hold Backspace, type
//   tripleClk  triple-click, type            <- the gesture that produced the concatenation
//
//   T4A=http://127.0.0.1:8795 node human-edit.mjs
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");

const HOST = process.env.T4A || "http://127.0.0.1:8795";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SEL = "#thinker-endpoint";
const TYPED = "http://127.0.0.1:8901/v1";

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 950 });
await p.goto(HOST, { waitUntil: "networkidle2" });
await sleep(800);
await p.evaluate(() => document.querySelector('button.cog-btn[title="Settings"]')?.click());
await sleep(900);

// The whole question is whether a PRE-FILLED field can be replaced, so an empty field measures
// nothing. The first version of this probe read seeded "" and passed three times on an empty box.
// Wait for the app to seed it; if it never does, seed it here -- and say which happened, because a
// field the app leaves empty is a different product than one it pre-fills.
let seeded = "";
let seededBy = "app";
for (let i = 0; i < 40 && !seeded; i++) { seeded = await p.$eval(SEL, (el) => el.value); if (!seeded) await sleep(250); }
if (!seeded) {
  seededBy = "probe";
  seeded = "https://mcp.tina4.com/v1";
  await p.evaluate((s, v) => {
    const el = document.querySelector(s);
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, SEL, seeded);
  await sleep(300);
}
if (!seeded) { console.log("  FAIL — the field is empty and cannot be seeded; replacement is unmeasurable"); await b.close(); process.exit(1); }
const results = [];

async function gesture(name, fn) {
  // Put the field back to the seeded value between gestures, the same way a reload would.
  await p.evaluate((s, v) => {
    const el = document.querySelector(s);
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, SEL, seeded);
  await sleep(200);
  await fn();
  await sleep(300);
  const got = await p.$eval(SEL, (el) => el.value);
  results.push({ gesture: name, value: got, clean: got === TYPED, appended: got === seeded + TYPED });
}

await gesture("ctrlA", async () => {
  await p.click(SEL);
  await p.keyboard.down("Control"); await p.keyboard.press("KeyA"); await p.keyboard.up("Control");
  await p.type(SEL, TYPED);
});

await gesture("backspace", async () => {
  await p.click(SEL);
  await p.keyboard.press("End");
  for (let i = 0; i < seeded.length + 5; i++) await p.keyboard.press("Backspace");
  await p.type(SEL, TYPED);
});

await gesture("tripleClk", async () => {
  await p.click(SEL, { clickCount: 3 });
  await p.type(SEL, TYPED);
});

// Does the field fight back? A binding that re-asserts the old value would show up as the typed
// text surviving keystroke-by-keystroke but being reverted a moment later.
await p.evaluate((s, v) => {
  const el = document.querySelector(s);
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(el, v);
  el.dispatchEvent(new Event("input", { bubbles: true }));
}, SEL, seeded);
await p.click(SEL);
await p.keyboard.down("Control"); await p.keyboard.press("KeyA"); await p.keyboard.up("Control");
await p.type(SEL, TYPED);
const rightAfter = await p.$eval(SEL, (el) => el.value);
await sleep(2500);
const twoSecondsLater = await p.$eval(SEL, (el) => el.value);

console.log(`  seeded value       ${JSON.stringify(seeded)}  (seeded by the ${seededBy})`);
for (const x of results) {
  const verdict = x.clean ? "CLEAN   " : x.appended ? "APPENDED" : "OTHER   ";
  console.log(`  ${verdict} ${x.gesture.padEnd(10)} ${JSON.stringify(x.value)}`);
}
console.log(`  no revert          ${rightAfter === twoSecondsLater ? "yes" : `NO -- ${JSON.stringify(rightAfter)} became ${JSON.stringify(twoSecondsLater)}`}`);

const humanGestures = results.filter((x) => x.gesture !== "tripleClk");
const ok = seeded.length > 0 && humanGestures.every((x) => x.clean) && rightAfter === twoSecondsLater;
console.log(`\n  ${ok ? "PASS" : "FAIL"} — a person CAN${ok ? "" : "NOT"} replace the pre-filled endpoint`);
if (!results.find((x) => x.gesture === "tripleClk").clean)
  console.log("  note: triple-click alone does not select here under headless chromium — that is the probe artefact");
await b.close();
process.exit(ok ? 0 : 1);
