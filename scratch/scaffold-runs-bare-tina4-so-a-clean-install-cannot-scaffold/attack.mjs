// Attacking the run-22 fix. Every cell is a machine where the tina4 CLI is ONLY at
// ~/.tina4-simple-agent/bin -- the download location, never on PATH -- with this host's
// /usr/local/bin masked, so nothing can pass for the wrong reason.
//
// The axes: is the `tina4` in command position or not; does a guard have to fire BEFORE the
// rewrite; is the binary path quotable; is the CLI reachable at all.
import { box, TREE } from "./boxes.mjs";

const DL = ".tina4-simple-agent/bin/tina4";
const cells = [];
const cell = (name, fn) => cells.push({ name, fn });

// 1. THE GUARD MUST STILL FIRE. longRunningRefusal matches a command-position `tina4`; a
//    rewritten `"/path/tina4" serve` is not in that shape. Resolve before the refusal and
//    `tina4 serve` walks straight past it and hangs for the full 60s timeout.
cell("tina4 serve is still REFUSED, not rewritten and run", () => {
  const r = box({ where: DL, cmd: "tina4 serve --port 7148", maskUsrLocal: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === false && /^refused:/.test(String(r.error)), got: String(r.error).slice(0, 70) };
});
cell("cd backend && uv run tina4 serve is still REFUSED", () => {
  const r = box({ where: DL, cmd: "cd . && uv run tina4 serve --port 7148", maskUsrLocal: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === false && /^refused:/.test(String(r.error)), got: String(r.error).slice(0, 70) };
});

// 2. NOT COMMAND POSITION -> untouched, and no CLI bootstrap attempted.
cell("echo tina4 is not rewritten", () => {
  const r = box({ where: DL, cmd: "echo tina4", maskUsrLocal: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && r.cmdAsRun === "echo tina4" && /^tina4$/.test(String(r.stdout)), got: `${r.cmdAsRun} / ${r.stdout}` };
});
cell("a quoted tina4 inside a string is not rewritten", () => {
  const r = box({ where: DL, cmd: `echo "tina4 init python ."`, maskUsrLocal: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && r.cmdAsRun === `echo "tina4 init python ."`, got: r.cmdAsRun };
});
cell("./tina4 is not rewritten (a project-local file, not the CLI)", () => {
  const r = box({ where: DL, cmd: "./tina4 --version", maskUsrLocal: true });
  // There is no ./tina4, so this must FAIL to exec -- and fail complaining about "./tina4",
  // not about a rewritten absolute path. Asserting the error text, not the absence of one.
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === false && /\.\/tina4/.test(String(r.error)) && !/\.tina4-simple-agent/.test(String(r.error)), got: `ok=${r.ok} err=${String(r.error).split("\n").join(" | ").slice(0, 80)}` };
});

// 3. EVERY COMMAND-POSITION HIT, not just the first.
cell("two tina4 segments are both rewritten", () => {
  const r = box({ where: DL, cmd: "tina4 migrate; tina4 seed", maskUsrLocal: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && r.fakeRuns === 2 && (String(r.cmdAsRun).match(/\.tina4-simple-agent/g) || []).length === 2, got: `${r.cmdAsRun} -> ran ${r.fakeRuns}x` };
});
cell("uv run + VAR= prefix still finds the tina4 behind it", () => {
  const r = box({ where: DL, cmd: "TINA4_DATABASE_URL=sqlite:///x.db uv run tina4 migrate", maskUsrLocal: true, withUv: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && r.fakeRuns === 1 && /uv run "[^"]*\.tina4-simple-agent[^"]*" migrate/.test(String(r.cmdAsRun)), got: `${r.cmdAsRun} -> ran ${r.fakeRuns}x` };
});

// 4. QUOTING. The rewrite splices `"${bin}"`. A $HOME with a space in it is the cheapest way to
//    find out whether that survives the shell.
cell("a binary path containing a space still executes", () => {
  const r = box({ where: DL, cmd: "tina4 init python .", maskUsrLocal: true, homeSpace: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && /FAKE_TINA4_RAN/.test(String(r.stdout)), got: `${r.cmdAsRun} -> ${r.stdout || String(r.error).split("\n")[0]}` };
});

// 5. NO CLI AND NO NETWORK. Must name the problem and settle, never hang.
cell("no CLI, no network: a named error, not a hang", () => {
  const started = Date.now();
  const r = box({ where: null, cmd: "tina4 init python .", maskUsrLocal: true, noNetwork: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  const ms = Date.now() - started;
  return { pass: r.ok === false && ms < 90_000, got: `${ms}ms — ${String(r.error).split("\n")[0].slice(0, 80)}` };
});

// 6. THE HAND-DELIVERED BUNDLE, with the guard on top of it.
cell("bundled CLI beside the executable is reached", () => {
  const r = box({ where: null, cmd: "tina4 init python .", maskUsrLocal: true, bundled: true });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && /FAKE_TINA4_RAN/.test(String(r.stdout)), got: `${r.cmdAsRun}` };
});

// 7. THE PATH ARM. A CLI in a directory that is on PATH but is not one of the fixed candidates
//    must still be found -- and must be found AS ITSELF, not swapped for something else.
cell("a CLI reachable only through PATH is resolved to that same binary", () => {
  const r = box({ where: null, cmd: "tina4 init python .", maskUsrLocal: true, extraPathDir: "mybin" });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && r.fakeRuns === 1 && /\/mybin\/tina4/.test(String(r.cmdAsRun)), got: String(r.cmdAsRun) };
});

// 8. PRECEDENCE, recorded rather than discovered later. With a CLI in BOTH a fixed candidate
//    directory and a PATH-only directory, tina4Candidates() puts the fixed one first -- so the
//    rewrite can run a DIFFERENT binary from the one a bare `tina4` would have. Same precedence
//    spawn_service has always used; this cell exists so the behaviour is written down.
cell("fixed candidate beats PATH when both hold a CLI (documented precedence)", () => {
  const r = box({ where: DL, cmd: "tina4 init python .", maskUsrLocal: true, extraPathDir: "mybin" });
  if (r.noJson) return { noJson: true, raw: r.raw };
  return { pass: r.ok === true && /\.tina4-simple-agent/.test(String(r.cmdAsRun)) && !/\/mybin\//.test(String(r.cmdAsRun)), got: String(r.cmdAsRun) };
});

console.log(`tree  ${TREE}\n`);
let bad = 0;
for (const c of cells) {
  let out;
  try { out = c.fn(); } catch (e) { out = { pass: false, got: `threw: ${e.message}` }; }
  // A cell that could not run is a FAILURE, never a pass. The secret-dialog probe passed three
  // checks on an untouched tree this way -- nothing ran, nothing contradicted the assertion.
  if (out.noJson) out = { pass: false, got: `PROBE DID NOT RUN -- ${out.raw}` };
  if (!out.pass) bad++;
  console.log(`${out.pass ? "PASS" : "FAIL"}  ${c.name}\n        ${out.got}`);
}
console.log(`\n${cells.length - bad}/${cells.length} cells pass`);
process.exit(bad ? 1 : 0);
