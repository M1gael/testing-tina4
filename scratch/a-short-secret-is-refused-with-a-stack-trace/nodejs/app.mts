// TREE_ND is substituted by prove.sh: the tina4-nodejs source tree to run.
import { get, startServer } from "TREE_ND/packages/core/src/index.ts";
get("/hello", async (req, res) => res.text("ok"));
await startServer({});
