// Runs ONE tool call against the tree named by T4_TREE, in whatever env the parent handed us,
// and prints a JSON line. Separate process on purpose: tools.ts computes TINA4_BIN_DIR from
// os.homedir() at IMPORT time, so HOME has to be right before the module is loaded.
const tree = process.env.T4_TREE;
// The app widens PATH at boot (app.ts:151) before any tool runs. Do the same, or the
// reproduction describes a machine that never exists.
if (process.env.T4_WIDEN === "1") { const { widenPath } = await import("./widen-path.mjs"); widenPath(); }
const { runTool, usesTina4Cli, resolveTina4InCommand, tina4Present } = await import(`${tree}/src/app/tools.ts`);
const { mkdtempSync, rmSync } = await import("node:fs");
const os = await import("node:os"); const path = await import("node:path");

const cmd = process.argv[2];
const dir = mkdtempSync(path.join(os.tmpdir(), "t4-run22-"));
const ctx = { workspaceRoot: dir, mcp: { url: "", token: "" }, service: { current: null }, onServiceChange: () => {} };

const CAP_MS = 60_000;
let out;
try {
  const r = await Promise.race([
    runTool("run_shell", { cmd }, ctx),
    // .unref() matters: without it this timer holds the event loop open for the full cap even
    // after the race has already settled, and every run costs CAP_MS of wall clock.
    new Promise((_, rj) => { const t = setTimeout(() => rj(new Error(`exceeded ${CAP_MS}ms`)), CAP_MS); t.unref(); }),
  ]);
  const present = tina4Present();
  out = {
    ok: r.ok,
    error: String(r.error || "").slice(0, 120),
    exitCode: r.result?.exitCode,
    cmdAsRun: String(r.result?.cmd ?? ""),
    stderr: String(r.result?.stderr || "").trim().split("\n")[0]?.slice(0, 120) ?? "",
    stdout: String(r.result?.stdout || "").trim().split("\n")[0]?.slice(0, 120) ?? "",
    fakeRuns: (String(r.result?.stdout || "").match(/FAKE_TINA4_RAN/g) || []).length,
    pathSeen: process.env.PATH,
    usesTina4Cli: usesTina4Cli(cmd),
    tina4Present: present,
    wouldRewriteTo: present ? resolveTina4InCommand(cmd, present) : null,
  };
} catch (e) {
  out = { ok: false, error: String(e.message), capped: true };
}
rmSync(dir, { recursive: true, force: true });
console.log("__JSON__" + JSON.stringify(out));
