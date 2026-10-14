// TREE_ND is substituted by prove.sh: the tina4-nodejs source tree to run.
import { get, post, startServer } from "TREE_ND/packages/core/src/index.ts";
post("/echo", async (req: any, res: any) => res.json({ body: req.body })).noAuth();
get("/q", async (req: any, res: any) => res.json({ query: req.query })).noAuth();
await startServer({});
