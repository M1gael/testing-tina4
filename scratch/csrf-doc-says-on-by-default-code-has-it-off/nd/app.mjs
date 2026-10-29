import { Router, startServer, getToken } from "tina4-nodejs";
Router.get("/ping", async (req, res) => res.json({ pong: true }));
// a logged-in browser: identity token held in the session, no Bearer
Router.get("/login", async (req, res) => { req.session.set("token", getToken({ user_id: 1 })); return res.json({ logged_in: true }); });
Router.get("/profile", async (req, res) => res.render("profile.twig", {}));
Router.post("/api/profile", async (req, res) => res.json({ saved: true })); // default write route: auth required
Router.post("/api/open", async (req, res) => res.json({ saved: true })).noAuth(); // ch10 exercise shape
await startServer({ port: Number(process.env.PORT), basePath: process.cwd(), noBrowser: true });
