// COMPONENT GATING for the dx-04 fix.
//
// The thing that must go red is not a suite assertion — it is /tmp itself. So each cleanup is
// reverted on its own, its suite is run, and the leftover directories are COUNTED. A component
// that leaves nothing behind when reverted was doing nothing.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";

const TREE = process.argv[2] || "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const abs = (f) => path.join(TREE, f);
const sum = (f) => createHash("sha256").update(readFileSync(abs(f))).digest("hex");

const PREFIXES = ["t4a-guards-", "t4a-state-", "t4a-harness-", "wc-"];
const leftovers = () => readdirSync("/tmp").filter((n) => PREFIXES.some((p) => n.startsWith(p))).map((n) => "/tmp/" + n);
const sweep = () => { for (const d of leftovers()) rmSync(d, { recursive: true, force: true }); };

const COMPONENTS = [
  ["write-guards cleanup", "test/write-guards.mjs", ["test/write-guards.mjs"],
    'const leftover = await cleanupTempDirs();\nif (leftover.length) { failed.push("temp workspaces removed"); console.log("  \\u2717 temp workspaces removed\\n      still on disk:", leftover.join(", ")); }\nelse { pass++; console.log("  \\u2713 temp workspaces removed, verified by reading"); }\n\n',
    ''],
  ["write-checks cleanup", "test/write-checks.mjs", ["test/write-checks.mjs"],
    'const leftover = await cleanupTempDirs();\nif (leftover.length) { console.log("  \\u2717 temp dir removed\\n      still on disk:", leftover.join(", ")); process.exit(1); }\nconsole.log("  \\u2713 temp dir removed, verified by reading");\n\n',
    ''],
  ["turn-harness cleanup", "test/turn-harness.mjs", ["test/turn-harness.mjs"],
    '    const leftover = await cleanupTempDirs();\n    check("temp dirs removed", leftover.length === 0, leftover.join(", "));',
    '    try { await fs.rm(PROJECTS, { recursive: true, force: true }); } catch {}'],
];

const FILES = [...new Set(COMPONENTS.flatMap((c) => c[2]))];
const ORIGINAL = Object.fromEntries(FILES.map((f) => [f, readFileSync(abs(f))]));
const SUM0 = Object.fromEntries(FILES.map((f) => [f, sum(f)]));

const run = (suite) => spawnSync("npx", ["tsx", suite], { cwd: TREE, encoding: "utf8", timeout: 600_000 });

sweep();
if (leftovers().length) { console.log("VERDICT: CANNOT GATE — /tmp is not clean before the run."); process.exit(2); }

let gated = 0;
for (const [name, suite, files, fixed, shipped] of COMPONENTS) {
  const f = files[0];
  const src = readFileSync(abs(f), "utf8");
  if (src.split(fixed).length - 1 !== 1) { console.log(`  ✗ ${name}: REVERT FAILED — text occurs ${src.split(fixed).length - 1} times`); continue; }
  writeFileSync(abs(f), src.replace(fixed, shipped));
  const r = run(suite);
  const left = leftovers();
  writeFileSync(abs(f), ORIGINAL[f]);
  if (sum(f) !== SUM0[f]) { console.log(`ABORT: ${f} did not restore.`); process.exit(2); }
  const ok = left.length > 0;
  if (ok) gated++;
  console.log(`  ${ok ? "✓" : "✗"} ${name}: reverted → ${left.length} leftover${left.length === 1 ? "" : "s"} (suite exit ${r.status})${ok ? "" : "  ← STAYED CLEAN, so it was doing nothing"}`);
  sweep();
}

// And with everything in place, nothing is left at all.
const full = run("test/write-guards.mjs").status === 0 && run("test/write-checks.mjs").status === 0 && run("test/turn-harness.mjs").status === 0;
const after = leftovers();
console.log(`\nfix in place: all three suites ${full ? "green" : "NOT green"}, ${after.length} leftover directories`);
console.log(`${gated}/${COMPONENTS.length} components gate.`);
const pass = gated === COMPONENTS.length && full && after.length === 0;
console.log(pass ? "VERDICT: every cleanup is load-bearing, and the run leaves /tmp clean."
                 : "VERDICT: FAIL — see above.");
process.exit(pass ? 0 : 1);
