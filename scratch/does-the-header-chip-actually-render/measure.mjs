import puppeteer from "/var/home/work/gitdir/tina4-simple-agent-work/scratch/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";
const b = await puppeteer.launch({ executablePath:"/usr/bin/chromium-browser", headless:true, args:["--no-sandbox"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 900 });
await p.goto(`http://127.0.0.1:${process.argv[2]}/`, { waitUntil:"networkidle2", timeout:30000 });
await new Promise(r=>setTimeout(r,2500));
console.log(JSON.stringify(await p.evaluate(()=>{
  const chip=document.querySelector(".model-chip"), tr=document.querySelector(".top-right");
  const cs=getComputedStyle(chip);
  return {
    topRightW: tr.getBoundingClientRect().width,
    topRightOverflow: tr.scrollWidth > tr.clientWidth + 1,
    chipW: chip.getBoundingClientRect().width, chipScroll: chip.scrollWidth, chipClient: chip.clientWidth,
    chipMaxW: cs.maxWidth, chipFlexShrink: cs.flexShrink, chipMinW: cs.minWidth,
    parts: [...chip.querySelectorAll(".mc-part")].map(e=>({ t:e.textContent.trim().slice(0,24), w:e.getBoundingClientRect().width, scroll:e.scrollWidth, client:e.clientWidth, shrink:getComputedStyle(e).flexShrink })),
  };
}),null,1));
await b.close();
