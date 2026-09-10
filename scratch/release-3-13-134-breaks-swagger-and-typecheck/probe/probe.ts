/**
 * What does a browser actually GET when swagger is on?
 * Boots the sandbox tree once per env case and reports the whole surface:
 * the UI page, the document, and -- the point -- whether the URL the served
 * page asks for is itself reachable.
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
    s.listen(0, "127.0.0.1", () => {
      const p = (s.address() as any).port;
      s.close(() => res(p));
    });
    s.on("error", rej);
  });

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function scaffold(): string {
  const root = mkdtempSync(join(tmpdir(), "t4-probe-"));
  mkdirSync(join(root, "src", "routes", "api", "items"), { recursive: true });
  writeFileSync(join(root, "package.json"), '{"name":"probe","type":"module","private":true}\n');
  writeFileSync(join(root, "src", "routes", "api", "items", "get.ts"),
    "export default async function (_req: any, res: any) { return res.json([]); }\n");
  writeFileSync(join(root, "app.ts"),
    `import { startServer } from '${REPO}/packages/core/src/index.ts';\n` +
    `await startServer({ port: Number(process.env.PORT), basePath: '${root}' } as never);\n`);
  return root;
}

async function probe(label: string, env: Record<string, string>) {
  const root = scaffold();
  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const fd = openSync(join(root, "server.log"), "w");
  const childEnv: Record<string, string> = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (v !== undefined && !k.startsWith("TINA4_SWAGGER_") && !k.startsWith("SWAGGER_") && k !== "TINA4_DEBUG") childEnv[k] = v;
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
    if (!up) { console.log(`${label}: SERVER NEVER CAME UP\n${readFileSync(join(root, "server.log"), "utf8").slice(-800)}`); return; }

    const banner = readFileSync(join(root, "server.log"), "utf8").includes("Swagger:   http://");

    const ui = await fetch(`${base}/swagger`);
    const html = await ui.text();
    const placeholder = html.includes("{SWAGGER_ROUTE}");
    const m = html.match(/url:\s*"([^"]+)"/);
    const asks = m ? m[1] : "(no url: found)";

    const doc = await fetch(`${base}/swagger/openapi.json`);
    await doc.arrayBuffer().catch(() => {});

    // The point: fetch exactly what the served page asks for.
    let round = "n/a";
    if (m && !placeholder) {
      const rr = await fetch(new URL(asks, base));
      await rr.arrayBuffer().catch(() => {});
      round = String(rr.status);
    } else if (placeholder) {
      const rr = await fetch(new URL(asks.replace("{SWAGGER_ROUTE}", "/swagger"), base));
      await rr.arrayBuffer().catch(() => {});
      round = `${rr.status} (placeholder substituted by hand)`;
    }

    console.log(
      `${label}\n` +
      `   banner advertises swagger : ${banner}\n` +
      `   GET /swagger             : ${ui.status}  placeholder=${placeholder}  asks for "${asks}"\n` +
      `   GET /swagger/openapi.json: ${doc.status}\n` +
      `   page's own url resolves  : ${round}\n`,
    );
  } finally {
    try { process.kill(-child.pid!, "SIGKILL"); } catch {}
  }
}

const cases: Array<[string, Record<string, string>]> = JSON.parse(process.env.CASES!);
for (const [label, env] of cases) await probe(label, env);
