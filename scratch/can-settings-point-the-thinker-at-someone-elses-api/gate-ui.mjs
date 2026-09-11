// w-20 UI GATE -- drives the REAL Settings screen, because the request was about Settings:
// "in the settings where you choose a thinker and coder, id really like the option to add API keys".
// gate.mjs proves the server honours a custom provider; this proves a person can reach it.
//
// Pinned on #thinker-endpoint / #thinker-token -- elements that do not exist on the untouched tree,
// so nothing here can be satisfied by the coder fields that have always been there.
//
//   T4A=http://127.0.0.1:8795 node gate-ui.mjs
import { createRequire } from "node:module";
const puppeteer = createRequire("/var/home/work/gitdir/tina4-simple-agent-work/scratch/package.json")("puppeteer-core");

const HOST = process.env.T4A || "http://127.0.0.1:8795";
const ENDPOINT = process.env.T4_ENDPOINT || "http://127.0.0.1:8901/v1";
const MODEL = "deepseek-reasoner";
const KEY = process.env.T4_KEY || "sk-UIGATE-fixed-key";   // shared with fake-provider.mjs by the runner
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const api = () => fetch(`${HOST}/api/model`).then((r) => r.json());

const b = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: "new",
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"] });
const p = await b.newPage();
let nativeDialogs = 0;
p.on("dialog", async (d) => { nativeDialogs++; await d.dismiss(); });
await p.setViewport({ width: 1400, height: 950 });
await p.goto(HOST, { waitUntil: "networkidle2" });
await sleep(800);

const r = {};
const before = await api();
r.shippedThinkerEndpoint = before.thinker?.endpoint;
r.shippedThinkerVendor = before.thinkerVendor;

// Open Settings the way a person does.
r.settingsOpened = await p.evaluate(() => {
  const btn = document.querySelector('button.cog-btn[title="Settings"]') || [...document.querySelectorAll("button")].find((b) => /settings/i.test(b.title || ""));
  if (!btn) return false; btn.click(); return true;
});
await sleep(900);

// The three thinker fields, which have never existed before this feature.
r.thinkerFieldsExist = await p.evaluate(() => !!document.querySelector("#thinker-endpoint") && !!document.querySelector("#thinker-model") && !!document.querySelector("#thinker-token"));
r.thinkerKeyIsMasked = await p.evaluate(() => document.querySelector("#thinker-token")?.type || "(absent)");
r.customOfferedForThinker = await p.evaluate(() => {
  const sels = [...document.querySelectorAll("select.mdl-select")];
  return sels.some((s) => [...s.options].some((o) => o.value === "custom:"));
});

if (!r.thinkerFieldsExist) {
  console.log(JSON.stringify(r, null, 1));
  console.log("\n  FAIL — the thinker fields do not exist; nothing further can be driven");
  await b.close(); process.exit(1);
}

// Type a provider in, exactly as a user would.
// Triple-click does NOT reliably select the contents of an input whose value is set by a property
// binding -- the first run of this gate typed INTO the existing value and read back
// "https://mcp.tina4.com/v1http://127.0.0.1:8901/v1", which looks like a broken build and was a
// broken probe. Clear through the native setter (so the framework sees a real input event), then type.
const type = async (sel, v) => {
  await p.evaluate((s) => {
    const el = document.querySelector(s);
    const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    set.call(el, "");
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, sel);
  await p.type(sel, v);
};
await type("#thinker-endpoint", ENDPOINT);
await type("#thinker-model", MODEL);
await type("#thinker-token", KEY);

// Pick "Custom (API key)" for the THINKER role. The thinker select is the one whose label says so.
r.pickedCustom = await p.evaluate(() => {
  const labels = [...document.querySelectorAll("label.vendor-pick")];
  const lbl = labels.find((l) => /thinker/i.test(l.querySelector("span")?.textContent || ""));
  const sel = lbl?.querySelector("select.mdl-select");
  if (!sel) return false;
  sel.value = "custom:";
  sel.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
});
await sleep(1200);

const after = await api();
r.thinkerVendorNow = after.thinkerVendor;
r.thinkerEndpointNow = after.thinker?.endpoint;
r.thinkerModelNow = after.thinker?.model;

// The key must not be observable anywhere in the page, and must not come back from the API.
r.keyInPageText = await p.evaluate((k) => document.body.innerText.includes(k), KEY);
r.keyInValueAttr = await p.evaluate((k) => [...document.querySelectorAll("input")].some((i) => (i.getAttribute("value") || "").includes(k)), KEY);
r.keyInOuterHtml = await p.evaluate((k) => document.documentElement.outerHTML.includes(k), KEY);
r.keyInApiResponse = (await fetch(`${HOST}/api/model`).then((x) => x.text())).includes(KEY);
r.nativeDialogs = nativeDialogs;

// The coder must be untouched by a thinker-only change -- the two roles are independent.
r.coderEndpointNow = after.endpoint;
r.coderVendorNow = after.coderVendor;

// "Test" -- part (e) of this feature's gate in FEATURES.md. A wrong key has to fail HERE, visibly,
// and not as a 401 three rounds into a build. Driven through the button a person clicks.
r.testButtons = await p.evaluate(() => [...document.querySelectorAll(".provider-test button")].map((b) => b.textContent.trim()));
await type("#thinker-token", "sk-DEFINITELY-WRONG");
r.testClicked = await p.evaluate(() => {
  const btns = [...document.querySelectorAll(".provider-test button")];
  const b = btns.find((x) => /thinker/i.test(x.textContent));
  if (!b) return false; b.click(); return true;
});
for (let i = 0; i < 40; i++) {
  await sleep(250);
  const t = await p.evaluate(() => document.querySelector(".provider-test .provider-test-result")?.textContent?.trim() || "");
  if (t) break;
}
r.testVerdict = await p.evaluate(() => {
  const el = [...document.querySelectorAll(".provider-test")].find((d) => /thinker/i.test(d.querySelector("button")?.textContent || ""));
  const out = el?.querySelector(".provider-test-result");
  return { text: (out?.textContent || "").replace(/\s+/g, " ").trim(), cls: out?.className || "" };
});
// Testing must not save. The selection made above must survive a failed test untouched.
const afterTest = await api();
r.selectionSurvivedTest = afterTest.thinker?.endpoint === ENDPOINT && afterTest.thinkerVendor === "custom";
r.nativeDialogsAfterTest = nativeDialogs;

for (const [k, v] of Object.entries(r)) console.log(`  ${k.padEnd(26)} ${JSON.stringify(v)}`);

const checks = [
  ["1 the thinker fields exist at all", r.thinkerFieldsExist === true],
  ["2 the thinker key field is masked", r.thinkerKeyIsMasked === "password"],
  ["3 Custom is offered in the role dropdown", r.customOfferedForThinker === true],
  ["4 picking Custom points the thinker at it", r.thinkerVendorNow === "custom" && r.thinkerEndpointNow === ENDPOINT && r.thinkerModelNow === MODEL],
  ["5 the key renders nowhere", r.keyInPageText === false && r.keyInValueAttr === false && r.keyInOuterHtml === false],
  ["6 no GET returns the key", r.keyInApiResponse === false],
  ["7 the coder is left alone", r.coderVendorNow !== "custom" && r.coderEndpointNow === before.endpoint],
  ["8 no native dialogs", r.nativeDialogs === 0 && r.nativeDialogsAfterTest === 0],
  ["9 there is a Test button for each role", Array.isArray(r.testButtons) && r.testButtons.length === 2],
  ["10 a wrong key fails visibly in Settings, and saves nothing",
   r.testClicked === true && /bad/.test(r.testVerdict?.cls || "") && /401|incorrect|unauthor/i.test(r.testVerdict?.text || "") && r.selectionSurvivedTest === true],
];
console.log();
for (const [n, ok] of checks) console.log(`  ${ok ? "ok  " : "FAIL"}  ${n}`);
const pass = checks.every((c) => c[1]);
console.log(`\n  ${pass ? "PASS" : "FAIL"} — ${checks.filter((c) => c[1]).length}/${checks.length}`);
await b.close();
process.exit(pass ? 0 : 1);
