// COMPONENT GATING for the sec-03 fix.
//
// One revert of the whole change proves very little. Each piece is reverted to exactly the
// expression that shipped, on its own, and the suite must go RED for that piece alone. A piece
// that stays green is either untested or dead weight, and the run says which.
//
// Every revert is undone and the file checksum re-read afterwards; a failed restore aborts the
// whole run rather than poisoning every component after it.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";

const TREE = process.argv[2] || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const FILES = ["app.ts", "src/app/tools.ts"];
const abs = (f) => path.join(TREE, f);
const sum = (f) => createHash("sha256").update(readFileSync(abs(f))).digest("hex");
const ORIGINAL = Object.fromEntries(FILES.map((f) => [f, readFileSync(abs(f))]));
const SUM0 = Object.fromEntries(FILES.map((f) => [f, sum(f)]));

// [name, file, fixed-text, shipped-text-it-replaced, which cells must go red]
const COMPONENTS = [
  ["state dir resolved once", "app.ts",
    'const APP_STATE_DIR = stateDir();',
    'const APP_STATE_DIR = process.env.TINA4_STATE_DIR\n  ? (process.env.TINA4_STATE_DIR.startsWith("~") ? path.join(os.homedir(), process.env.TINA4_STATE_DIR.slice(1)) : process.env.TINA4_STATE_DIR)\n  : path.join(os.homedir(), ".tina4-simple-agent");'],
  ["anthropic key read path", "app.ts",
    '  const secretsDir = globalSecretsDir();',
    '  const secretsDir = path.join(os.homedir(), ".tina4-simple-agent", "secrets");'],
  ["global secrets write path", "app.ts",
    '  const dir = globalSecretsDir();\n  await fs.mkdir(dir, { recursive: true, mode: 0o700 });',
    '  const dir = path.join(os.homedir(), ".tina4-simple-agent", "secrets");\n  await fs.mkdir(dir, { recursive: true, mode: 0o700 });'],
  ["vision readSecret", "src/app/tools.ts",
    'path.join(globalSecretsDir(), name)',
    'path.join(os.homedir(), ".tina4-simple-agent", "secrets", name)'],
  ["get_secret candidate path", "src/app/tools.ts",
    '    const globalAbs = path.join(globalSecretsDir(), secretName);',
    '    const globalAbs = path.join(os.homedir(), ".tina4-simple-agent", "secrets", secretName);'],
  ["get_secret scope label", "src/app/tools.ts",
    'scope: abs === globalAbs ? "global" : "project"',
    'scope: abs.includes(".tina4-simple-agent") ? "global" : "project"'],
];

const runSuite = () => {
  const r = spawnSync("npx", ["tsx", "test/state-dir-isolation.mjs"], { cwd: TREE, encoding: "utf8", timeout: 120_000 });
  return { code: r.status, out: (r.stdout || "") + (r.stderr || "") };
};

const base = runSuite();
console.log(`baseline (fix in place): exit ${base.code} — ${base.out.trim().split("\n").pop()}`);
if (base.code !== 0) { console.log("VERDICT: CANNOT GATE — the suite is not green before any revert."); process.exit(2); }

const rows = [];
for (const [name, file, fixed, shipped] of COMPONENTS) {
  const src = readFileSync(abs(file), "utf8");
  if (src.split(fixed).length - 1 !== 1) {
    console.log(`  ✗ ${name}: REVERT FAILED — its text occurs ${src.split(fixed).length - 1} times, expected exactly 1`);
    rows.push([name, "REVERT FAILED", ""]); continue;
  }
  writeFileSync(abs(file), src.replace(fixed, shipped));
  const r = runSuite();
  writeFileSync(abs(file), ORIGINAL[file]);
  if (sum(file) !== SUM0[file]) { console.log(`ABORT: ${file} did not restore byte-for-byte.`); process.exit(2); }
  const last = r.out.trim().split("\n").filter((l) => l.includes("state-dir-isolation:")).pop() || r.out.trim().split("\n").pop();
  rows.push([name, r.code === 0 ? "STAYED GREEN" : "went red", last]);
  console.log(`  ${r.code === 0 ? "✗" : "✓"} ${name}: ${r.code === 0 ? "STAYED GREEN (untested or dead)" : "went red"} — ${last}`);
}

for (const f of FILES) if (sum(f) !== SUM0[f]) { console.log(`ABORT: ${f} left modified.`); process.exit(2); }
const ungated = rows.filter((r) => r[1] !== "went red");
console.log(`\n${rows.length - ungated.length}/${rows.length} components gate.`);
console.log(ungated.length ? `VERDICT: ${ungated.length} NOT gated by this suite: ${ungated.map((r) => r[0] + " (" + r[1] + ")").join(", ")}`
                           : "VERDICT: every component of the fix is gated — each one alone turns the suite red.");
process.exit(ungated.length ? 1 : 0);
