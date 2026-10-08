// One SMTP send from tina4-nodejs's Messenger; prints elapsed seconds and the outcome.
// Usage: node --import <tsx loader> send.mts <tree> <host> <port> [option-json]
const [tree, host, port, extra] = process.argv.slice(2);
const { Messenger } = await import(`${tree}/packages/core/src/index.ts`);
const options = { host, port: Number(port), fromAddress: "app@localhost", encryption: "none", ...(extra ? JSON.parse(extra) : {}) };
const start = Date.now();
let outcome: string;
try {
  const r = await new Messenger(options).send("someone@localhost", "test", "hello");
  outcome = `success=${r.success} message=${r.message}`;
} catch (e) {
  outcome = `threw ${(e as Error).name}: ${(e as Error).message}`;
}
console.log(`ELAPSED=${((Date.now() - start) / 1000).toFixed(1)}s OUTCOME=${outcome}`);
process.exit(0);
