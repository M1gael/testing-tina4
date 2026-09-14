// run-20's last unverified claim: app.ts:3002 and src/app/streamers.ts:225 send
// stream_options:{include_usage:true} on every streamed call. That field has only ever been
// sent to a FAKE gateway. If the REAL gateway rejects an unknown body field, streaming --
// plan authoring and chat replies -- breaks for every user.
//
// Two cells, same endpoint, same model, same tiny prompt:
//   A  with stream_options   -> must be 200, must stream, must carry a usage block
//   B  without (control)     -> tells us whether any failure in A is the field or the gateway
// A cell that cannot run FAILS. No silent pass.
const ENDPOINT = process.env.EP || "https://mcp.tina4.com/v1";
const TOKEN    = process.env.TK || "FREE-TOKEN";
const MODEL    = process.env.MD || "tina4-thinker";
const CAP_MS   = 90_000;

async function cell(name, withOpts) {
  const body = {
    model: MODEL,
    messages: [{ role: "system", content: "Answer with one word." },
               { role: "user", content: "Say OK." }],
    temperature: 0.7, top_p: 0.95,
    max_tokens: 32,               // app sends >=16000; cap size is irrelevant to field acceptance
    stream: true,
    ...(withOpts ? { stream_options: { include_usage: true } } : {}),
  };
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), CAP_MS);
  const out = { name, status: null, err: null, chunks: 0, usage: null, text: "" };
  try {
    const r = await fetch(ENDPOINT.replace(/\/+$/, "") + "/chat/completions", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${TOKEN}`, accept: "text/event-stream" },
      body: JSON.stringify(body), signal: ac.signal,
    });
    out.status = r.status;
    if (!r.ok) { out.err = (await r.text()).slice(0, 400); return out; }
    if (!r.body) { out.err = "200 but no body stream"; return out; }
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = "";
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
        if (!line.startsWith("data:")) continue;
        const d = line.slice(5).trim(); if (d === "[DONE]") continue;
        let j; try { j = JSON.parse(d); } catch { continue; }
        out.chunks++;
        if (j.usage) out.usage = j.usage;
        const c = j.choices?.[0]?.delta ?? {};
        out.text += c.content ?? c.reasoning_content ?? c.reasoning ?? "";
      }
    }
  } catch (e) {
    out.err = (e && e.name === "AbortError") ? `aborted at cap ${CAP_MS}ms` : String(e && e.message || e);
  } finally { clearTimeout(timer); }
  return out;
}

const A = await cell("A with stream_options", true);
const B = await cell("B control, no stream_options", false);
for (const c of [A, B]) {
  console.log(`${c.name}: status=${c.status} chunks=${c.chunks} usage=${c.usage ? JSON.stringify(c.usage) : "none"} text=${JSON.stringify(c.text.slice(0,60))}${c.err ? " err=" + JSON.stringify(c.err) : ""}`);
}
const accepted  = A.status === 200 && A.chunks > 0 && !A.err;
const gotUsage  = !!(A.usage && (Number(A.usage.total_tokens) > 0 ||
                    (Number(A.usage.prompt_tokens) || 0) + (Number(A.usage.completion_tokens) || 0) > 0));
const controlOK = B.status === 200 && B.chunks > 0 && !B.err;
console.log(`\nfield accepted (200 + streamed): ${accepted}`);
console.log(`usage block with a positive total: ${gotUsage}`);
console.log(`control streamed without the field: ${controlOK}`);
console.log(accepted && gotUsage
  ? "VERDICT: PASS -- real gateway accepts stream_options and returns usage. run-20 claim closed by running."
  : `VERDICT: FAIL -- ${!controlOK ? "control also failed, so this is the gateway/network, NOT the field" : "the field itself is the problem"}.`);
process.exit(accepted && gotUsage ? 0 : 1);
