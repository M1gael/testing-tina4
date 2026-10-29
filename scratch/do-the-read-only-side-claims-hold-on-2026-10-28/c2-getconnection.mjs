// claim 2: Database.getConnection() opens a NEW connection and replaces the global adapter per call.
// Control: initDatabase once + getAdapter() twice returns the same adapter (the instrument can see "same").
const T = process.env.ND_TREE;
const { Database, getAdapter } = await import(T + "/packages/orm/dist/index.js");
process.env.TINA4_DATABASE_URL = "sqlite::memory:";
const a = await Database.getConnection(); const ga = getAdapter();
await a.execute("CREATE TABLE t (x INTEGER)"); await a.execute("INSERT INTO t VALUES (1)");
const b = await Database.getConnection(); const gb = getAdapter();
let seen; try { seen = (await b.fetch("SELECT x FROM t")).records.length; } catch (e) { seen = "ERR " + e.message.split("\n")[0]; }
const ctl1 = getAdapter(), ctl2 = getAdapter();
console.log(`same_db=${a === b} global_replaced=${ga !== gb} second_sees_first_table=${seen} control_getAdapter_same=${ctl1 === ctl2}`);
