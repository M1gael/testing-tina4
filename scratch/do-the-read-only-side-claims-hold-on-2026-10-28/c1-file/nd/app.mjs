const { Router, startServer } = await import(process.env.ND_TREE + "/packages/core/dist/index.js");
const REPORT = process.env.REPORT;
Router.get("/ping", async (req, res) => res.json({ pong: true }));
// ch03 nodejs doc, verbatim call shape: res.file(path, "custom-name.pdf")
Router.get("/doc", async (req, res) => res.file(REPORT, "monthly-report-march-2026.pdf"));
// control: the real signature (options object)
Router.get("/ok", async (req, res) => res.file(REPORT, { download: true }));
await startServer({ port: Number(process.env.PORT), basePath: process.cwd(), noBrowser: true });
