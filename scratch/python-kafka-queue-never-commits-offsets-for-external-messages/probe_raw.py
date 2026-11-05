"""Raw-socket path (no confluent-kafka): external records get distinct job ids, complete() does not raise.
Usage: python probe_raw.py <src root>"""
import os, sys, secrets
sys.path.insert(0, sys.argv[1])
from tina4_python.queue import Queue
from tina4_python.queue_backends.kafka_backend import KafkaConnector
t = "q274r_" + secrets.token_hex(4)
KafkaConnector().enqueue(t, {"n": 0}, add_id=False); KafkaConnector().enqueue(t, {"n": 1}, add_id=False)
q = Queue(topic=t, backend="kafka"); assert not q._backend._backend._use_confluent
jobs = [q.pop(), q.pop()]
for j in jobs: j.complete()
print("raw ids", [j.id for j in jobs], [j.payload for j in jobs])
