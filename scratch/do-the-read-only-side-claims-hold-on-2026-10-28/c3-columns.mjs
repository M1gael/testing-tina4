// claim 3: createTable() before any instance -> camelCase columns; save() writes snake_case.
// arg "instance-first" = control: construct one instance with data before createTable().
const T = process.env.ND_TREE;
const { initDatabase, BaseModel } = await import(T + "/packages/orm/dist/index.js");
const db = await initDatabase({ url: "sqlite::memory:" });
class Post extends BaseModel {
  static tableName = "posts";
  static fields = {
    id:       { type: "integer", primaryKey: true, autoIncrement: true },
    authorId: { type: "integer" },
    title:    { type: "string" },
  };
}
if (process.argv[2] === "instance-first") new Post({ authorId: 0, title: "" });
await Post.createTable();
const cols = (await db.fetch("SELECT name FROM pragma_table_info('posts')")).records ?? [];
let saved;
try { const p = await Post.create({ authorId: 7, title: "t" }); saved = "ok id=" + p.id; }
catch (e) { saved = "ERR " + String(e.message).split("\n")[0]; }
const n = (await db.fetch("SELECT COUNT(*) AS n FROM posts")).records[0].n;
console.log(`columns=${cols.map(c => c.name).join(",")} save=${saved} rows=${n}`);
