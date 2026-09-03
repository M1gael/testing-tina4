import { JSONRPCMessageSchema, InitializeResultSchema, ListToolsResultSchema }
  from '/var/home/work/.npm/_npx/1e7f6d9597241db0/node_modules/@modelcontextprotocol/sdk/dist/esm/types.js';
import fs from 'node:fs';
const R = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const SP = process.env.SP;
const init = R(`${SP}/init.raw`), tools = R(`${SP}/toolslist.raw`), err = R(`${SP}/unknownmethod.raw`);
const SIG = init.signature;
const env = m => JSONRPCMessageSchema.safeParse(m).success;
const clone = o => JSON.parse(JSON.stringify(o));

const drop = clone(init); delete drop.signature;
const inres = clone(init); delete inres.signature; inres.result.signature = SIG;
const inmeta = clone(init); delete inmeta.signature; inmeta.result._meta = { signature: SIG };
const errdrop = clone(err); delete errdrop.signature;
const errres = clone(err); delete errres.signature; errres.result = { signature: SIG };
const errdata = clone(err); delete errdata.signature; errdata.error.data = { signature: SIG };
const errinner = clone(err); delete errinner.signature; errinner.error.signature = SIG;
const tdrop = clone(tools); delete tdrop.signature;
const tinres = clone(tools); delete tinres.signature; tinres.result.signature = SIG;

const rows = [
  ['as-shipped   initialize', env(init)],
  ['as-shipped   tools/list', env(tools)],
  ['as-shipped   error      ', env(err)],
  ['FIX-A drop       initialize', env(drop)],
  ['FIX-A drop       tools/list', env(tdrop)],
  ['FIX-A drop       error     ', env(errdrop)],
  ['FIX-B result.sig initialize', env(inres)],
  ['FIX-B result.sig tools/list', env(tinres)],
  ['FIX-B result.sig ON ERROR (adds result+error)', env(errres)],
  ['FIX-C result._meta.sig     ', env(inmeta)],
  ['FIX-D error.data.sig       ', env(errdata)],
  ['FIX-E error.signature      ', env(errinner)],
];
for (const [n, ok] of rows) console.log((ok ? 'PASS ' : 'FAIL ') + n);

console.log('--- result-level schemas (after envelope) ---');
console.log('InitializeResultSchema  w/ result.signature :', InitializeResultSchema.safeParse(inres.result).success);
console.log('ListToolsResultSchema   w/ result.signature :', ListToolsResultSchema.safeParse(tinres.result).success);
console.log('--- does error.signature survive parse? ---');
const p = JSONRPCMessageSchema.safeParse(errinner);
console.log('kept keys on error obj:', p.success ? Object.keys(p.data.error) : 'n/a');
