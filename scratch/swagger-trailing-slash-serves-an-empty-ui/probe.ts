/**
 * f-sw-02: what does GET /swagger/ actually serve?
 *
 * Run against a tree that ALREADY has the f-sw-01 guard fix, because on the
 * published 3.13.134 both paths are broken and this defect cannot be seen
 * separately.
 *
 *   SB=<tree> tsx probe.ts
 *
 * Reports, per env case, the trailing-slash form of a swagger path and of a
 * PLAIN APP path. The plain path is the control: it separates "this framework
 * does not do trailing slashes by default" from "swagger specifically serves a
 * broken page".
 */
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, openSync, closeSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:net";

const REPO = process.env.SB!;
const TSX = join(REPO, "node_modules", ".bin", "tsx");

const freePort = (): Promise<number> =>
  new Promise((res, rej) => {
    const s = createServer();
    s.listen(0, "127.0.0.1", () => { const p = (s.address() as any).port; s.close(() => res(p)); });
    s.on("error", rej);
  });
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function scaffold(): string {
  const root = mkdtempSync(join(tmpdir(), "t4-sw02-"));
  mkdirSync(join(root, "src", "routes", "api", "items"), { recursive: true });
  writeFileSync(join(root, "package.json"), '{"name":"sw02","type":"module","private":true}\n');
  writeFileSync(join(root, "src", "routes", "api", "items", "get.ts"),
    "export default async function (_req: any, res: any) { return res.json([]); }\n");
  writeFileSync(join(root, "app.ts"),
    `import { startServer } from '${REPO}/packages/core/src/index.ts';\n` +
    `await startServer({ port: Number(process.env.PORT), basePath: '${root}' } as never);\n`);
  return root;
}

/** status + whether the body is the dead bundled asset. Never follows redirects. */
async function get(base: string, path: string) {
  const r = await fetch(base + path, { redirect: "manual" });
  const ct = r.headers.get("content-type") ?? "";
  const body = ct.includes("html") || ct.includes("json") || ct.includes("text") ? await r.text() : (await r.arrayBuffer(), "");
  return {
    status: r.status,
    location: r.headers.get("location"),
    placeholder: body.includes("{SWAGGER_ROUTE}"),
    asks: (body.match(/url:\s*"([^"]+)"/) ?? [, null])[1] as string | null,
  };
}

async function run(label: string, env: Record<string, string>) {
  const root = scaffold();
  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const fd = openSync(join(root, "server.log"), "w");
  const childEnv: Record<string, string> = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (v !== undefined && !k.startsWith("TINA4_SWAGGER_") && !k.startsWith("SWAGGER_") && k !== "TINA4_DEBUG" && k !== "TINA4_TRAILING_SLASH_REDIRECT") childEnv[k] = v;
  }
  Object.assign(childEnv, { PORT: String(port), TINA4_NO_AI_PORT: "true", TINA4_NO_BROWSER: "true", TINA4_OVERRIDE_CLIENT: "true", ...env });
  const child = spawn(TSX, ["app.ts"], { cwd: root, detached: true, stdio: ["ignore", fd, fd], env: childEnv });
  closeSync(fd);
  try {
    const deadline = Date.now() + 60_000;
    let up = false;
    while (Date.now() < deadline) {
      try { const r = await fetch(`${base}/api/items`); await r.arrayBuffer().catch(() => {}); if (r.status === 200) { up = true; break; } } catch {}
      await sleep(250);
    }
    if (!up) { console.log(`${label}: NEVER CAME UP\n${readFileSync(join(root, "server.log"), "utf8").slice(-900)}`); return; }
    console.log(`\n${label}`);
    for (const p of ["/swagger", "/swagger/", "/api/items", "/api/items/"]) {
      const r = await get(base, p);
      console.log(`   ${p.padEnd(14)} ${String(r.status).padEnd(4)}` +
        `${r.location ? ` -> ${r.location}` : ""}` +
        `${r.placeholder ? "  DEAD-PLACEHOLDER" : ""}` +
        `${r.asks ? `  asks:${r.asks}` : ""}`);
    }
  } finally { try { process.kill(-child.pid!, "SIGKILL"); } catch {} }
}

const cases: Array<[string, Record<string, string>]> = [
  ["swagger on, trailing-slash redirect DEFAULT (unset)", { TINA4_SWAGGER_ENABLED: "true" }],
  ["swagger on, TINA4_TRAILING_SLASH_REDIRECT=true", { TINA4_SWAGGER_ENABLED: "true", TINA4_TRAILING_SLASH_REDIRECT: "true" }],
  ["swagger OFF, redirect default", { TINA4_SWAGGER_ENABLED: "false" }],
];
for (const [l, e] of cases) await run(l, e);
