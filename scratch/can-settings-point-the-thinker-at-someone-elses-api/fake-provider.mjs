// A stand-in OpenAI-compatible provider, for the UI gate. Answers plausibly enough that the app
// does not read it as an offline stub, and records nothing -- gate-ui asserts on the app's own
// state, not on what arrived here (gate.mjs is the one that reads the wire).
import http from "node:http";
const PORT = Number(process.argv[2] || 8901);
// argv[3], when given, is the only key this provider accepts. Without it "Test with a wrong key
// fails" cannot be demonstrated -- a provider that accepts everything has no failure to show.
const KEY = process.argv[3] || "";
const sse = (res, o) => res.write(`data: ${JSON.stringify(o)}\n\n`);
http.createServer((req, res) => {
  if (req.method === "GET") {
    if (KEY && req.headers.authorization !== `Bearer ${KEY}`) {
      res.writeHead(401, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: { message: "Incorrect API key provided", code: "invalid_api_key" } })); return;
    }
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ data: [{ id: "deepseek-reasoner", context_window: 64000 }] })); return;
  }
  let body = ""; req.on("data", (c) => (body += c));
  req.on("end", () => {
    let b = null; try { b = JSON.parse(body); } catch {}
    const maxTok = Number(b?.max_tokens ?? 0);
    const sys = String(b?.messages?.[0]?.content ?? "");
    const answer = maxTok > 0 && maxTok <= 8 ? "QUESTION"
      : /\bJSON\b/i.test(sys) ? '{"action":"answer","files":[],"acceptance":"","locate":""}'
      : "A small static page.";
    if (b && b.stream === false) {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ choices: [{ message: { role: "assistant", content: answer } }], usage: { prompt_tokens: 5, completion_tokens: 5, total_tokens: 10 } })); return;
    }
    res.writeHead(200, { "content-type": "text/event-stream" });
    sse(res, { choices: [{ delta: { role: "assistant" } }] });
    sse(res, { choices: [{ delta: { content: answer } }] });
    sse(res, { choices: [{ delta: {}, finish_reason: "stop" }] });
    res.write("data: [DONE]\n\n"); res.end();
  });
}).listen(PORT, "127.0.0.1", () => console.log("fake provider on " + PORT));
