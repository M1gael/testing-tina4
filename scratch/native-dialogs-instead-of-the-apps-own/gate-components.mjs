// COMPONENT GATING for the ui-05 slice-3 fix. Each piece is reverted to the behaviour it
// replaced, ALONE, and the browser gate must go red for that piece. A piece that stays green is
// either untested or was never doing anything.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";

const TREE = process.argv[2] || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const PORT = process.argv[3] || "8935";
const GATE = path.join(path.dirname(new URL(import.meta.url).pathname), "gate-ui.mjs");
const FILES = ["public/app.js", "public/style.css"];
const abs = (f) => path.join(TREE, f);
const sum = (f) => createHash("sha256").update(readFileSync(abs(f))).digest("hex");
const ORIGINAL = Object.fromEntries(FILES.map((f) => [f, readFileSync(abs(f))]));
const SUM0 = Object.fromEntries(FILES.map((f) => [f, sum(f)]));

const COMPONENTS = [
  ["dialog paints above other modals", "public/style.css",
   '.modal-backdrop.dialog-backdrop { z-index: 120; background: rgba(20, 22, 28, 0.45); }',
   '.modal-backdrop.dialog-backdrop { background: rgba(20, 22, 28, 0.45); }'],
  ["Escape is owned in the capture phase", "public/app.js",
   'window.addEventListener("keydown", this._esc, true);\n  }\n  onUnmount() { window.removeEventListener("keydown", this._esc, true); }',
   'window.addEventListener("keydown", this._esc);\n  }\n  onUnmount() { window.removeEventListener("keydown", this._esc); }'],
  ["Escape does not propagate to the modal below", "public/app.js",
   'e.preventDefault(); e.stopPropagation();',
   'e.preventDefault();'],
  ["the queue, rather than one slot", "public/app.js",
   'dialogQueue.value = [...dialogQueue.value, { ...req, resolve, id: ++pushDialog.n }]',
   'dialogQueue.value = [{ ...req, resolve, id: ++pushDialog.n }]'],
  ["focus follows the head of the queue", "public/app.js",
   'if (this._focused !== top.id) {',
   'if (false) {'],
];

const run = () => {
  const r = spawnSync("npx", ["tsx", GATE, ".", PORT], { cwd: TREE, encoding: "utf8", timeout: 600_000 });
  const out = (r.stdout || "") + (r.stderr || "");
  const line = out.split("\n").filter((l) => /^\d+\/\d+ passed/.test(l)).pop() || "no result line";
  const red = out.split("\n").filter((l) => l.startsWith("❌")).map((l) => l.split("  —")[0].replace("❌ ", ""));
  return { code: r.status, line, red };
};

const base = run();
console.log(`baseline (fix in place): exit ${base.code} — ${base.line}`);
if (base.code !== 0) { console.log("VERDICT: CANNOT GATE — not green before any revert.\n  " + base.red.join("\n  ")); process.exit(2); }

let gated = 0;
for (const [name, file, fixed, shipped] of COMPONENTS) {
  const src = readFileSync(abs(file), "utf8");
  if (src.split(fixed).length - 1 !== 1) { console.log(`  ✗ ${name}: REVERT FAILED — text occurs ${src.split(fixed).length - 1} times`); continue; }
  writeFileSync(abs(file), src.replace(fixed, shipped));
  const r = run();
  writeFileSync(abs(file), ORIGINAL[file]);
  if (sum(file) !== SUM0[file]) { console.log(`ABORT: ${file} did not restore.`); process.exit(2); }
  const ok = r.code !== 0;
  if (ok) gated++;
  console.log(`  ${ok ? "✓" : "✗"} ${name}: ${ok ? "went red" : "STAYED GREEN (untested or dead)"} — ${r.line}${r.red.length ? "\n        " + r.red.join("\n        ") : ""}`);
}
for (const f of FILES) if (sum(f) !== SUM0[f]) { console.log(`ABORT: ${f} left modified.`); process.exit(2); }
console.log(`\n${gated}/${COMPONENTS.length} components gate.`);
process.exit(gated === COMPONENTS.length ? 0 : 1);
