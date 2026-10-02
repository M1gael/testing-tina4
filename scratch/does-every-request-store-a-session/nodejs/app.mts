// TREE_ND is substituted by prove.sh: the tina4-nodejs source tree to run.
import { get, startServer } from "TREE_ND/packages/core/src/index.ts";
get("/where", async (req, res) => res.text(import.meta.resolve("TREE_ND/packages/core/src/session.ts")));
get("/plain", async (req, res) => res.text("plain"));   // never touches the session
get("/read", async (req, res) => res.text("user=" + (req.session.get("user") ?? "-")));
get("/write", async (req, res) => { req.session.set("user", "alice"); return res.text("wrote"); });
get("/login", async (req, res) => {   // regenerate, then set
  req.session.regenerate(); req.session.set("user", "alice"); return res.text("logged in");
});
get("/flash-set", async (req, res) => { req.session.flash("notice", "saved"); return res.text("flashed"); });
get("/flash-get", async (req, res) => res.text("flash=" + (req.session.getFlash("notice") ?? "-")));
await startServer({});
