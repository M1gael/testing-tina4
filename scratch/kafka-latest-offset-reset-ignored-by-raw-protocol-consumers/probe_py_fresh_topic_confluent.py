"""Reference: the same 'consumer starts before the topic exists' case on the
confluent-kafka path. Usage: python probe_py_fresh_topic_confluent.py <src> <reset>"""
import os, sys, secrets
sys.path.insert(0, sys.argv[1])
os.environ["TINA4_KAFKA_AUTO_OFFSET_RESET"] = sys.argv[2]
from tina4_python.queue_backends.kafka_backend import KafkaConnector
b = os.environ["TINA4_KAFKA_BROKERS"]
topic = "frq01_freshc_" + secrets.token_hex(4)
cons = KafkaConnector(brokers=b, group_id="frq01_g_" + secrets.token_hex(4)); prod = KafkaConnector(brokers=b)
seen = [cons.dequeue(topic)]
prod.enqueue(topic, {"n": "first"})
for _ in range(8):
    m = cons.dequeue(topic); seen.append(m and m["n"])
    if m: break
print(f"confluent reset={sys.argv[2]} seen={seen}")
