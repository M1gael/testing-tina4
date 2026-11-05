// Usage: node collect.mjs <tina4-css tree, or a dir holding frond.js>  (jsdom resolved from that tree's node_modules, else $JSDOM_FROM)
// Runs the built frond.js in jsdom and compares frond.form.collect() with what a
// native form submission would send (new FormData(form)), cell by cell.
import { createRequire } from "node:module";
import { readFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
const tree = resolve(process.argv[2]);
const file = existsSync(join(tree, "dist", "frond.js")) ? join(tree, "dist", "frond.js") : join(tree, "frond.js");
const require = createRequire(join(resolve(process.env.JSDOM_FROM || tree), "package.json"));
const { JSDOM } = require("jsdom");
const cells = {
  "multiple, two selected":   `<select multiple name="g[]"><option value="1" selected>A</option><option value="2" selected>B</option><option value="3">C</option></select>`,
  "multiple, none selected":  `<select multiple name="g[]"><option value="1">A</option><option value="2">B</option></select>`,
  "multiple, one selected":   `<select multiple name="g[]"><option value="1">A</option><option value="2" selected>B</option></select>`,
  "multiple, no [] in name":  `<select multiple name="g"><option value="1" selected>A</option><option value="2" selected>B</option></select>`,
  "multiple, empty value":    `<select multiple name="g[]"><option value="" selected>none</option><option value="2" selected>B</option></select>`,
  "multiple, text as value":  `<select multiple name="g[]"><option selected>Alpha</option><option selected>Beta</option></select>`,
  "multiple, nested in fieldset":`<fieldset><select multiple name="g[]"><option value="1" selected>A</option><option value="2" selected>B</option></select></fieldset>`,
  "single select":            `<select name="s"><option value="1">A</option><option value="2" selected>B</option></select>`,
  "single, nothing chosen":   `<select name="s"><option value="1">A</option><option value="2">B</option></select>`,
  "text + checkbox + radio":  `<input name="t" value="x"><input type="checkbox" name="c" value="on" checked><input type="radio" name="r" value="b" checked><textarea name="ta">hi</textarea>`,
};
let bad = 0;
const src = readFileSync(file, "utf8");
for (const [label, html] of Object.entries(cells)) {
  const dom = new JSDOM(`<!doctype html><body><form id="f">${html}</form></body>`, { runScripts: "outside-only" });
  dom.window.eval(src);
  const pairs = (fd) => JSON.stringify([...fd.entries()]);
  const got = pairs(dom.window.frond.form.collect("f"));
  const want = pairs(new dom.window.FormData(dom.window.document.getElementById("f")));
  const ok = got === want;
  if (!ok) bad++;
  console.log(`${ok ? "ok  " : "FAIL"} ${label}: collect=${got}${ok ? "" : ` native=${want}`}`);
}
console.log(`${file}: ${bad} cell(s) differ from a native submit`);
process.exit(bad ? 1 : 0);
