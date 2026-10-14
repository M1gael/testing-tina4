// Stock tina4-nodejs v3: AutoCrud + toCrud over a 3-row sqlite table.
import { existsSync, rmSync } from "node:fs";
import { startServer } from "@tina4/core";
import { initDatabase, getAdapter, registerBackend } from "@tina4/orm";
import Person from "./src/models/Person.ts";

if (existsSync("people.db")) rmSync("people.db");
await initDatabase({ url: "sqlite:///people.db" } as any);
const db: any = getAdapter();
db.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)");
for (const [n, a] of [["Ann", 30], ["O'Brien", 40], ["Zed", 25]]) db.execute("INSERT INTO people (name, age) VALUES (?, ?)", [n, a]);
db.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT)");
db.execute("INSERT INTO secrets (id, token) VALUES (1, 'TOPSECRET')");
await registerBackend(Person as any, { public: true });
await startServer({ port: Number(process.env.PORT ?? 7464), host: "127.0.0.1" });
