// Does <span class="usage-total"> render the tok/s, given it passes a thunk where its siblings
// pass values? Serve public/ + tina4js, fixture /api/model with a real non-zero cost, look.
import http from "node:http";
import { readFileSync, statSync } from "node:fs";
import { join, extname } from "node:path";
import puppeteer from "/var/home/work/gitdir/tina4-simple-agent-work/scratch/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";
const root = "/var/home/work/gitdir/tina4-simple-agent-work/scratch";
const TYPES = { ".html":"text/html", ".js":"text/javascript", ".css":"text/css", ".svg":"image/svg+xml", ".png":"image/png" };
const COST = { total:{calls:5,tokensIn:24638,tokensOut:2878,ms:178076}, byVendor:{ local:{calls:5,tokensIn:24638,tokensOut:2878,ms:178076} }, byActor:{} };
const MODEL = { version:"0.2.0", workspace:"/tmp/w", projectsRoot:"/tmp/p", currentProject:"",
  model:"coder-model-x", thinker:{model:"thinker-model-y",endpoint:"e",preset:"custom"}, cost:COST };
const hit = (b,r)=>{ const f=join(b,r); try{ if(statSync(f).isFile()) return f; }catch{} return null; };
const srv = http.createServer((req,res)=>{ const p=new URL(req.url,"http://x").pathname;
  if(p.startsWith("/api/")){ res.writeHead(200,{"content-type":"application/json"}); return res.end(JSON.stringify(p==="/api/model"?MODEL:{})); }
  const f = p.startsWith("/js/") ? hit(join(root,"node_modules","tina4js","dist"), p.slice(4)) : hit(join(root,"public"), p==="/"?"index.html":p.slice(1));
  if(!f){ res.writeHead(404); return res.end("x"); }
  res.writeHead(200,{"content-type":TYPES[extname(f)]||"application/octet-stream"}); res.end(readFileSync(f)); });
await new Promise(r=>srv.listen(0,"127.0.0.1",r));
const browser = await puppeteer.launch({ executablePath:"/usr/bin/chromium-browser", headless:true, args:["--no-sandbox"] });
const page = await browser.newPage();
const errs=[]; page.on("pageerror",e=>errs.push(String(e.message).split("\n")[0]));
await page.goto(`http://127.0.0.1:${srv.address().port}/`,{waitUntil:"networkidle2",timeout:30000});
await new Promise(r=>setTimeout(r,2500));
console.log(JSON.stringify(await page.evaluate(()=>({
  stripExists: !!document.querySelector(".usage-strip"),
  total: document.querySelector(".usage-total")?.textContent.replace(/\s+/g," ").trim() ?? null,
  vendor: document.querySelector(".usage-vendor")?.textContent.replace(/\s+/g," ").trim() ?? null,
  html: document.querySelector(".usage-total")?.innerHTML.slice(0,300) ?? null,
})),null,1));
console.log("pageerrors:", errs.slice(0,3));
await browser.close(); srv.close();
