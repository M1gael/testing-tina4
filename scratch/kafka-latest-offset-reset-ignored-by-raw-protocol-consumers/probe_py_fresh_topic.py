"""Usage: python probe_py_fresh_topic.py <tina4-python src root> <latest|earliest>
Attack: a 'latest' consumer that starts BEFORE the topic exists. It dequeues
(nothing), then a record is produced, then it dequeues again. Reports what the
ListOffsets round trips answered and whether the first record was seen."""
import os, sys, secrets
sys.path.insert(0, sys.argv[1])
os.environ["TINA4_KAFKA_AUTO_OFFSET_RESET"] = sys.argv[2]
from tina4_python.queue_backends.kafka_backend import KafkaConnector
b = os.environ["TINA4_KAFKA_BROKERS"]
topic = "frq01_fresh_" + secrets.token_hex(4)
cons = KafkaConnector(brokers=b); prod = KafkaConnector(brokers=b)
for c in (cons, prod):
    c._use_confluent = False
answers = []
orig = getattr(cons, "_send_list_offsets", None)
if orig:
    cons._send_list_offsets = lambda t, ts: answers.append(orig(t, ts)) or answers[-1]
seen = [cons.dequeue(topic)]
prod.enqueue(topic, {"n": "first"})
for _ in range(4):
    m = cons.dequeue(topic); seen.append(m and m["n"])
    if m: break
print(f"reset={sys.argv[2]} list_offsets answers={answers} seen={seen}")
print("VERDICT", "PASS" if "first" in seen else "FAIL (first record on a new topic skipped)")
