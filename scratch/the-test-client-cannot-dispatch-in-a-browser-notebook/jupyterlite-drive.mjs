import { chromium } from "playwright-core";
const b = await chromium.launch({ executablePath: "/usr/local/bin/chromium", headless: true });
const p = await b.newPage();
p.on("pageerror", e => console.log("PAGEERR", String(e).slice(0,200)));
await p.goto(process.argv[2] + "/lab/index.html?path=probe.ipynb");
await p.waitForSelector(".jp-Notebook .jp-Cell", { timeout: 120000 });
await p.waitForTimeout(8000);
console.log("jupyterapp?", await p.evaluate(() => typeof window.jupyterapp));
await p.click(".jp-Notebook .jp-Cell .jp-InputArea-editor");
for (let i = 0; i < 8; i++) { await p.keyboard.press("Shift+Enter"); await p.waitForTimeout(700); }
const deadline = Date.now() + 240000;
let text = "";
while (Date.now() < deadline) {
  text = await p.evaluate(() => [...document.querySelectorAll(".jp-OutputArea-output")].map(e => e.innerText).join("\n----\n"));
  if (text.includes("END")) break;
  await p.waitForTimeout(3000);
}
console.log(text.split("\n").filter(l => !/^(Collecting|Downloading|Installing|Successfully)/.test(l)).join("\n").slice(0, 4000));
await b.close();
