"""Usage: python probe_py.py <tina4-python src root> <reset: latest|earliest>
Produces 3 'old' records to a fresh topic, then a NEW consumer (new group id,
env offset reset) dequeues; a 'new' record is produced; it dequeues again.
Prints the backend path (raw/confluent) and the sequence it saw."""
import os, sys, secrets, time
sys.path.insert(0, sys.argv[1])
reset = sys.argv[2]
from tina4_python.queue_backends.kafka_backend import KafkaConnector

brokers = os.environ["TINA4_KAFKA_BROKERS"]
topic = "frq01_py_" + secrets.token_hex(4)
os.environ.pop("TINA4_KAFKA_AUTO_OFFSET_RESET", None)
prod = KafkaConnector(brokers=brokers, group_id="frq01_prod_" + secrets.token_hex(4))
for i in range(3):
    prod.enqueue(topic, {"n": f"old-{i}"})
os.environ["TINA4_KAFKA_AUTO_OFFSET_RESET"] = reset
cons = KafkaConnector(brokers=brokers, group_id="frq01_grp_" + secrets.token_hex(4))
seen = []
m = cons.dequeue(topic)
seen.append(m and m.get("n"))
prod.enqueue(topic, {"n": "new"})
for _ in range(6):
    m = cons.dequeue(topic)
    seen.append(m and m.get("n"))
    if m and m.get("n") == "new":
        break
path = "confluent" if cons._use_confluent else "raw"
print(f"py[{path}] reset={reset} seen={seen}")
old = [s for s in seen if s and s.startswith("old")]
if reset == "latest":
    print("VERDICT", "PASS" if not old and "new" in seen else "FAIL (replayed backlog)" if old else "ERROR (new not seen)")
else:
    print("VERDICT", "PASS" if seen[0] == "old-0" else "FAIL")
prod.close(); cons.close()
