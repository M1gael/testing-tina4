/** Edge cells around the trailing-slash fix: odd path forms, odd methods, and
 *  the question the fix could plausibly have broken — does the new route leak
 *  into the generated document? */
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, openSync, closeSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:net";

const REPO = process.env.SB!;
const TSX = join(REPO, "node_modules", ".bin", "tsx");
const freePort = (): Promise<number> => new Promise((res, rej) => {
  const s = createServer();
  s.listen(0, "127.0.0.1", () => { const p = (s.address() as any).port; s.close(() => res(p)); });
  s.on("error", rej);
});
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

const root = mkdtempSync(join(tmpdir(), "t4-edges-"));
mkdirSync(join(root, "src", "routes", "api", "items"), { recursive: true });
writeFileSync(join(root, "package.json"), '{"name":"e","type":"module","private":true}\n');
writeFileSync(join(root, "src", "routes", "api", "items", "get.ts"),
  "export default async function (_req: any, res: any) { return res.json([]); }\n");
writeFileSync(join(root, "app.ts"),
  `import { startServer } from '${REPO}/packages/core/src/index.ts';\n` +
  `await startServer({ port: Number(process.env.PORT), basePath: '${root}' } as never);\n`);

const port = await freePort();
const base = `http://127.0.0.1:${port}`;
const fd = openSync(join(root, "server.log"), "w");
const env: Record<string, string> = {};
for (const [k, v] of Object.entries(process.env)) if (v !== undefined) env[k] = v;
Object.assign(env, { PORT: String(port), TINA4_SWAGGER_ENABLED: "true", TINA4_NO_AI_PORT: "true", TINA4_NO_BROWSER: "true", TINA4_OVERRIDE_CLIENT: "true" });
delete env.TINA4_TRAILING_SLASH_REDIRECT;
const child = spawn(TSX, ["app.ts"], { cwd: root, detached: true, stdio: ["ignore", fd, fd], env });
closeSync(fd);

const deadline = Date.now() + 60_000;
while (Date.now() < deadline) {
  try { const r = await fetch(`${base}/api/items`); await r.arrayBuffer().catch(() => {}); if (r.status === 200) break; } catch {}
  await sleep(250);
}

for (const [method, path] of [
  ["GET", "/swagger"], ["GET", "/swagger/"], ["GET", "/swagger//"], ["GET", "/SWAGGER/"],
  ["GET", "/swagger/index.html"], ["GET", "/swagger/oauth2-redirect.html"],
  ["HEAD", "/swagger/"], ["OPTIONS", "/swagger/"], ["POST", "/swagger/"],
  ["GET", "/swagger/openapi.json"], ["GET", "/swagger/openapi.json/"],
] as Array<[string, string]>) {
  const r = await fetch(base + path, { method, redirect: "manual" });
  const ct = r.headers.get("content-type") ?? "";
  const body = /html|json|text/.test(ct) && method !== "HEAD" ? await r.text() : (await r.arrayBuffer(), "");
  const flags = [
    body.includes("{SWAGGER_ROUTE}") ? "DEAD-PLACEHOLDER" : "",
    r.headers.get("location") ? `-> ${r.headers.get("location")}` : "",
    r.headers.get("allow") ? `allow:${r.headers.get("allow")}` : "",
  ].filter(Boolean).join("  ");
  console.log(`  ${method.padEnd(8)} ${path.padEnd(30)} ${String(r.status).padEnd(4)} ${flags}`);
}

const doc = await (await fetch(`${base}/swagger/openapi.json`)).json() as any;
const leaked = Object.keys(doc.paths ?? {}).filter((k) => k === "/swagger" || k.startsWith("/swagger"));
console.log(`\n  document paths: ${Object.keys(doc.paths ?? {}).join(", ")}`);
console.log(`  swagger paths leaked into the document: ${leaked.length === 0 ? "none" : leaked.join(", ")}`);

try { process.kill(-child.pid!, "SIGKILL"); } catch {}
