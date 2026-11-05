"""Tina4-produced jobs only: after q.dead_letters(), does q.pop() still read the main topic?
Usage: python probe_pop_after_dead_letters.py <src root>"""
import os, sys, secrets
sys.path.insert(0, sys.argv[1])
from tina4_python.queue import Queue
t = "q274s_" + secrets.token_hex(4); os.environ["TINA4_KAFKA_GROUP_ID"] = "q274sg_" + secrets.token_hex(4)
q = Queue(topic=t, backend="kafka", max_retries=3)
q.push({"n": "before"}); a = q.pop(); a.complete()
q.dead_letters()
q.push({"n": "after"})
b = q.pop(); c = q.pop() if b is None else None
print(f"before={a and a.payload} after_dead_letters={b and b.payload} second_try={c and c.payload}",
      "PASS" if (b or c) else "FAIL (main topic no longer read)")
q._backend._backend.close()
