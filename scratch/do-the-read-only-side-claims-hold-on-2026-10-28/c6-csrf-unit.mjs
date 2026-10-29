// claim 6 mechanism: call the BUILT CsrfMiddleware.beforeCsrf (which calls csrfRouteSkips) with the same
// tokenless POST, once carrying route metadata the way csrfRouteSkips reads it, once without (as server.ts sends it).
const { CsrfMiddleware } = await import(process.env.ND_TREE + "/packages/core/dist/index.js");
process.env.TINA4_CSRF = "true"; process.env.TINA4_SECRET = "0123456789abcdef0123456789abcdef0123456789abcdef";
function run(extra) {
  let status = "pass";
  const res = (body, code) => { status = code; return res; };
  const req = { method: "POST", headers: {}, query: {}, body: { name: "A" }, params: {}, ...extra };
  CsrfMiddleware.beforeCsrf(req, res);
  return status;
}
console.log(`with_route_noAuth=${run({ _route: { noAuth: true } })} with_route_alias=${run({ route: { noAuth: true } })} without=${run({})} route_noAuth_false=${run({ _route: { noAuth: false } })}`);
