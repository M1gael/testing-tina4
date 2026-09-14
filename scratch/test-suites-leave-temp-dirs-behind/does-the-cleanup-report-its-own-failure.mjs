// The worse half of dx-04 was not the leak, it was the SILENCE: `try { rm } catch {}` prints the
// same thing whether the directory went away or not. So the helper must be able to say "I could
// not remove this". A cleanup that cannot report its own failure is the defect wearing a fix.
//
// Make removal genuinely impossible — a child inside a read-only parent; POSIX needs write on the
// PARENT to unlink — then check the helper names the survivor instead of returning clean.
import { mkdirSync, chmodSync, rmSync, writeFileSync, existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";

if (process.getuid && process.getuid() === 0) {
  console.log("VERDICT: CANNOT RUN — running as root, which ignores the permission this test depends on.");
  process.exit(2);
}
// Resolved: a relative "." cannot be dynamically imported from, and the failure looks like a
// crash rather than a bad argument.
const TREE = path.resolve(process.argv[2] || "/var/home/work/gitdir/tina4-simple-agent-work/scratch");
const { tempPath, cleanupTempDirs } = await import(path.join(TREE, "test/tmpdirs.mjs"));

// The jail lives under os.tmpdir(), which is what tempPath() joins against, so the registered
// path names exactly the directory that cannot be removed.
const jail = path.join(os.tmpdir(), "t4a-cleanup-jail-" + process.pid);
const stuck = path.join(jail, "stuck");
mkdirSync(stuck, { recursive: true });
writeFileSync(path.join(stuck, "f"), "x");
chmodSync(jail, 0o555);

tempPath(path.join(path.basename(jail), "stuck"));
const survivors = await cleanupTempDirs();

chmodSync(jail, 0o755);
const stillThere = existsSync(stuck);
rmSync(jail, { recursive: true, force: true });

console.log(JSON.stringify({ survivors, stillThere, jailRemoved: !existsSync(jail) }, null, 1));
const reported = stillThere && survivors.includes(stuck);
console.log(reported
  ? "\nVERDICT: PASS — an unremovable directory comes back NAMED, not swallowed."
  : `\nVERDICT: FAIL — the directory ${stillThere ? "survived but was NOT reported" : "was removable, so this test proved nothing"}.`);
process.exit(reported ? 0 : 1);
