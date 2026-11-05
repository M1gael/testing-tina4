// Usage: node probe_nd.mjs <tina4-nodejs src root> <latest|earliest>
// Same scenario as probe_py.py, through KafkaBackend (raw protocol, the only path).
const [root, reset] = process.argv.slice(2);
const { KafkaBackend } = await import(root + "/packages/core/src/queueBackends/kafkaBackend.ts");
const brokers = process.env.TINA4_KAFKA_BROKERS;
const topic = "frq01_nd_" + Math.random().toString(16).slice(2, 10);
// The node backend never sends Metadata, so its produce cannot trigger topic
// auto-creation (upstream's own integration test pre-creates the topic). Send
// one Metadata v0 request here so the broker auto-creates it, then let the
// leader settle.
const net = await import("node:net");
await new Promise((resolve, reject) => {
  const [h, p] = brokers.split(":");
  const t = Buffer.from(topic), c = Buffer.from("probe");
  const body = Buffer.alloc(2 + 2 + 4 + 2 + c.length + 4 + 2 + t.length);
  let o = 0;
  o = body.writeInt16BE(3, o); o = body.writeInt16BE(0, o); o = body.writeInt32BE(1, o);
  o = body.writeInt16BE(c.length, o); c.copy(body, o); o += c.length;
  o = body.writeInt32BE(1, o); o = body.writeInt16BE(t.length, o); t.copy(body, o);
  const len = Buffer.alloc(4); len.writeInt32BE(body.length);
  const s = net.createConnection({ host: h, port: +p }, () => s.write(Buffer.concat([len, body])));
  s.once("data", () => { s.destroy(); resolve(); });
  s.on("error", reject);
});
await new Promise((r) => setTimeout(r, 1500));
delete process.env.TINA4_KAFKA_AUTO_OFFSET_RESET;
const prod = new KafkaBackend({ brokers, groupId: "frq01_prod" });
for (let i = 0; i < 3; i++) prod.push(topic, { n: `old-${i}` });
process.env.TINA4_KAFKA_AUTO_OFFSET_RESET = reset;
const cons = new KafkaBackend({ brokers, groupId: "frq01_grp_" + Math.random().toString(16).slice(2, 10) });
const n = (j) => (j ? (j.payload ?? j).n : null);
const seen = [n(cons.pop(topic))];
prod.push(topic, { n: "new" });
for (let k = 0; k < 6; k++) { const v = n(cons.pop(topic)); seen.push(v); if (v === "new") break; }
console.log(`nd[raw] reset=${reset} seen=${JSON.stringify(seen)}`);
const old = seen.filter((s) => s && s.startsWith("old"));
if (reset === "latest") console.log("VERDICT", !old.length && seen.includes("new") ? "PASS" : old.length ? "FAIL (replayed backlog)" : "ERROR (new not seen)");
else console.log("VERDICT", seen[0] === "old-0" && seen.includes("new") ? "PASS" : "FAIL");
