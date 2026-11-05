"""Usage: python probe_py_deadletters.py <tina4-python src root> <latest|earliest>
A dead-lettered job already sits on <topic>.dead_letter; a fresh Queue process
asks dead_letters(). The dead-letter list is a read of the whole DLQ, so it must
find the job whatever the offset-reset policy of the main consumer is."""
import os, sys, secrets
sys.path.insert(0, sys.argv[1])
reset = sys.argv[2]
from tina4_python.queue_backends.kafka_backend import KafkaConnector
from tina4_python.queue import Queue
topic = "frq01_dl_" + secrets.token_hex(4)
os.environ.pop("TINA4_KAFKA_AUTO_OFFSET_RESET", None)
prod = KafkaConnector(brokers=os.environ["TINA4_KAFKA_BROKERS"])
prod.enqueue(topic + ".dead_letter", {"id": "dead-1", "payload": {"x": 1}, "attempts": 9})
os.environ["TINA4_KAFKA_AUTO_OFFSET_RESET"] = reset
os.environ["TINA4_KAFKA_GROUP_ID"] = "frq01_dlgrp_" + secrets.token_hex(4)
q = Queue(topic=topic, backend="kafka", max_retries=3)
path = "confluent" if q._backend._backend._use_confluent else "raw"
dead = q.dead_letters()
ids = [getattr(j, "id", None) or (j.get("id") if isinstance(j, dict) else None) for j in dead]
print(f"py[{path}] reset={reset} dead_letters ids={ids}")
print("VERDICT", "PASS" if "dead-1" in ids else "FAIL (dead-lettered job not listed)")
