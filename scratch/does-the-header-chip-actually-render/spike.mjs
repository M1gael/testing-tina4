// Can a real Chrome render the harness header from public/ alone, with /api/* intercepted?
import http from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, extname } from "node:path";
import puppeteer from "/var/home/work/gitdir/tina4-simple-agent-work/scratch/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";

const PUB = "/var/home/work/gitdir/tina4-simple-agent-work/scratch/public";
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json" };
const MODEL = { model: "coder-model-x", thinker: { model: "thinker-model-y", endpoint: "http://127.0.0.1:11455/v1", preset: "custom" }, version: "0.0.0", workspace: "/tmp/w", projectsRoot: "/tmp/p", currentProject: "" };

const srv = http.createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  if (url.pathname.startsWith("/api/")) {
    const body = url.pathname === "/api/model" ? MODEL : {};
    res.writeHead(200, { "content-type": "application/json" }); return res.end(JSON.stringify(body));
  }
  const f = join(PUB, url.pathname === "/" ? "index.html" : url.pathname.slice(1));
  if (!existsSync(f)) { res.writeHead(404); return res.end("no"); }
  res.writeHead(200, { "content-type": TYPES[extname(f)] || "application/octet-stream" });
  res.end(readFileSync(f));
});
await new Promise(r => srv.listen(0, "127.0.0.1", r));
const port = srv.address().port;

const browser = await puppeteer.launch({ executablePath: "/usr/bin/chromium-browser", headless: true, args: ["--no-sandbox"] });
const page = await browser.newPage();
const errs = []; page.on("pageerror", e => errs.push(String(e.message).split("\n")[0]));
await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle2", timeout: 20000 });
await new Promise(r => setTimeout(r, 1500));
const out = await page.evaluate(() => ({
  chip: document.querySelector(".model-chip")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
  chipTitle: document.querySelector(".model-chip")?.getAttribute("title") ?? null,
  header: document.querySelector(".top-right")?.textContent?.replace(/\s+/g, " ").trim().slice(0, 160) ?? null,
}));
console.log(JSON.stringify(out, null, 1));
console.log("pageerrors:", errs.slice(0, 4));
await browser.close(); srv.close();
