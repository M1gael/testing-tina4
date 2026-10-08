// TREE_ND is substituted by prove.sh: the tina4-nodejs source tree to run.
import { get, startServer } from "TREE_ND/packages/core/src/index.ts";
get("/hello", async (req, res) => res.html("<!DOCTYPE html><html><head><title>hi</title></head><body><h1>hi</h1></body></html>"));
await startServer({});
