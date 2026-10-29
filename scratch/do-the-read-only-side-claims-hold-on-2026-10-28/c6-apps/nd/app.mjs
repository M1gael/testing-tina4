const { Router, startServer, getToken } = await import(process.env.ND_TREE + "/packages/core/dist/index.js");
Router.get("/ping", async (req, res) => res.json({ pong: true }));
Router.get("/login", async (req, res) => { req.session.set("token", getToken({ user_id: 1 })); return res.json({ logged_in: true }); });
Router.post("/api/save", async (req, res) => res.json({ saved: true }));
Router.post("/api/open", async (req, res) => res.json({ saved: true })).noAuth();
await startServer({ port: Number(process.env.PORT), basePath: process.cwd(), noBrowser: true });
