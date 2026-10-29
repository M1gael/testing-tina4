// Serves doc blocks written to ./gen by prove.sh, verbatim except model import paths.
// s1 = ch05 "Getting the Database Object" (registers its own Router.get)
// s2 = ch06 hasMany route, s3 = ch06 belongsTo route (default-export handlers)
// s4 = ch06 "create -- Build and Save in One Step" (top-level statement, result exported)
// s5 = ch07 "List Endpoint with Filters" (default-export handler)
import { startServer, Router } from "tina4-nodejs";
import { initDatabase } from "tina4-nodejs/orm";

const db = await initDatabase({ url: process.env.TINA4_DATABASE_URL });
const Author = (await import("./gen/models/Author.ts")).default;
const BlogPost = (await import("./gen/models/BlogPost.ts")).default;
const Note = (await import("./gen/models/Note.ts")).default;
// authors/posts by SQL: createTable() before any instance exists makes camelCase columns while save()
// writes snake_case (separate defect, see readme); the docs' own hasMany/belongsTo use "author_id".
await db.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, bio TEXT DEFAULT '', created_at TEXT)");
await db.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, author_id INTEGER, title TEXT, slug TEXT, content TEXT DEFAULT '', status TEXT DEFAULT 'draft', created_at TEXT, updated_at TEXT)");
await Note.createTable();
await db.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, created_at TEXT)");
await db.execute("INSERT INTO products (name, category, price) VALUES ('Keyboard','Electronics',79.99),('Desk','Furniture',549.99),('Mouse','Electronics',19.99)");
const alice = await Author.create({ name: "Alice", email: "alice@example.com" });
for (const t of ["Getting Started", "Advanced Routing"])
  await BlogPost.create({ authorId: alice.id, title: t, slug: t.toLowerCase().replace(/ /g, "-") });

await import("./gen/s1.ts");
Router.get("/api/authors/{id}", (await import("./gen/s2.ts")).default);
Router.get("/api/posts/{id}", (await import("./gen/s3.ts")).default);
Router.get("/api/products", (await import("./gen/s5.ts")).default);
Router.get("/s4", async (_req: any, res: any) => {
  const r = (await import("./gen/s4.ts")).result;
  return res.json({ isNote: r instanceof Note, id: r?.id ?? null });
});
await startServer({ port: Number(process.env.PORT), basePath: process.cwd(), noBrowser: true });
