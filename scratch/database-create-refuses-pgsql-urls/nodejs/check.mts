// tina4-nodejs parity for tina4-php#280: does Database.create() take a pgsql:// URL?
// Usage: node --import <tsx loader> check.mts <tina4-nodejs tree>
// Port 1 is closed, so an accepted scheme fails with a CONNECT error (ECONNREFUSED);
// a refused scheme fails before any connect.
const [tree] = process.argv.slice(2);
const orm = await import(`${tree}/packages/orm/src/index.ts`);
for (const url of ["pgsql://127.0.0.1:1/x", "postgres://127.0.0.1:1/x", "postgresql://127.0.0.1:1/x"]) {
  const engine = new orm.DatabaseUrl(url).engine;
  for (const [how, open] of [
    ["Database.create", () => orm.Database.create(url)],
    ["initDatabase({url})", () => orm.initDatabase({ url })],
  ] as const) {
    let outcome: string;
    try { await open(); outcome = "opened"; }
    catch (e) { const err = e as Error & { code?: string }; outcome = `${err.name}${err.code ? " " + err.code : ""}: ${err.message.slice(0, 70)}`; }
    console.log(`${url.padEnd(28)} DatabaseUrl engine=${engine}  ${how}: ${outcome}`);
  }
}
process.exit(0);
