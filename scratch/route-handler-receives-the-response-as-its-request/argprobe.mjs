// Runs the RELEASED invokeRouteHandler bytes from tina4-nodejs 3.13.103, verbatim.
import { readFileSync } from "node:fs";
const DIST = "./node_modules/tina4-nodejs/packages/core/dist/index.js";
const src = readFileSync(DIST, "utf8").split("\n");
const start = src.findIndex(l => l.includes("async function invokeRouteHandler"));
const body = src.slice(start, start + 14).join("\n");
console.log(`extracted dist lines ${start + 1}..${start + 14} from ${DIST}\n`);
const invokeRouteHandler = eval(`(${body.replace("async function invokeRouteHandler", "async function")})`);

const REQ = { __is: "REQUEST", params: {}, headers: {}, cookies: {}, session: {}, user: { sub: 42 } };
const RES = { __is: "RESPONSE", json: () => {}, raw: {} };

const cases = [
  ["(req, res)                 canonical", async (req, res) => ({ first: req?.__is, second: res?.__is })],
  ["(request, response)        canonical", async (request, response) => ({ first: request?.__is, second: response?.__is })],
  ["(ctx, res)                 renamed  ", async (ctx, res) => ({ first: ctx?.__is, second: res?.__is })],
  ["(e, t)                     minified ", async (e, t) => ({ first: e?.__is, second: t?.__is })],
  ["({ req, res })             destructured", async ({ req, res }) => ({ first: req?.__is, second: res?.__is })],
];

for (const [label, handler] of cases) {
  const out = await invokeRouteHandler({ handler }, REQ, RES);
  const ok = out?.first === "REQUEST" && out?.second === "RESPONSE";
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}  ->  arg0=${out?.first ?? "undefined"}  arg1=${out?.second ?? "undefined"}`);
}
