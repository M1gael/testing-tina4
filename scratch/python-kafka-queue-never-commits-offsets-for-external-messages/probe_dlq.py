"""External record: reject() and fail() past max_retries reach dead_letters with a usable id,
and retry_job(that id) moves it back. Usage: python probe_dlq.py <src root>"""
import os, sys, json, secrets
sys.path.insert(0, sys.argv[1])
from confluent_kafka import Producer
from tina4_python.queue import Queue
B = os.environ["TINA4_KAFKA_BROKERS"]
for act in ("reject", "fail"):
    t = "q274d_" + secrets.token_hex(4); os.environ["TINA4_KAFKA_GROUP_ID"] = "q274dg_" + secrets.token_hex(4)
    p = Producer({"bootstrap.servers": B}); p.produce(t, value=json.dumps({"n": act})); p.flush(10)
    q = Queue(topic=t, backend="kafka", max_retries=1)
    j = q.pop(); getattr(j, act)("x")
    dead = q.dead_letters()
    ids = [d.id if hasattr(d, "id") else d.get("id") for d in dead]
    ok = q.retry(ids[0]) if ids else False
    back = q.pop()
    print(f"{act}: job.id={j.id} dead_ids={ids} retry={ok} back={back and back.payload}")
    q._backend._backend.close()
