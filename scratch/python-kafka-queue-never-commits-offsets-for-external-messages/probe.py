"""Usage: python probe.py <tina4-python src root>
Needs confluent-kafka and TINA4_KAFKA_BROKERS. Each case uses a fresh topic and group.
Prints, per case, the group's committed offset after the consumer finished, and a verdict."""
import os, sys, json, secrets
sys.path.insert(0, sys.argv[1])
from confluent_kafka import Producer, Consumer, TopicPartition
from tina4_python.queue import Queue

B = os.environ["TINA4_KAFKA_BROKERS"]

def external(topic, values):
    p = Producer({"bootstrap.servers": B})
    for v in values:
        p.produce(topic, value=json.dumps(v))
    assert p.flush(10) == 0

def committed(topic, group):
    c = Consumer({"bootstrap.servers": B, "group.id": group})
    off = c.committed([TopicPartition(topic, 0)], timeout=10)[0].offset
    c.close()
    return off  # -1001 = nothing committed

def queue(topic, group):
    os.environ["TINA4_KAFKA_GROUP_ID"] = group
    return Queue(topic=topic, backend="kafka", max_retries=3)

def case(name, produce, consume, want):
    topic = "q274_" + secrets.token_hex(4); group = "q274g_" + secrets.token_hex(4)
    produce(topic)
    q = queue(topic, group)
    ids = consume(q)
    q._backend.close()
    got = committed(topic, group)
    print(f"{name:34} job_ids={ids} committed={got} want={want}  {'PASS' if got == want else 'FAIL'}")

def pop_all(q, n, act="complete"):
    ids = []
    for _ in range(n):
        j = q.pop()
        if j is None:
            ids.append(None); continue
        ids.append(j.id)
        getattr(j, act)()
    return ids

case("A external, complete x3",
     lambda t: external(t, [{"n": i} for i in range(3)]), lambda q: pop_all(q, 3), 3)
case("B tina4 push, complete x3",
     lambda t: [queue(t, "unused").push({"n": i}) for i in range(3)], lambda q: pop_all(q, 3), 3)
case("C external, fail x1 (retries left)",
     lambda t: external(t, [{"n": 0}]), lambda q: pop_all(q, 1, "fail"), 1)
def dup(q):
    j1, j2 = q.pop(), q.pop()
    j1.complete()          # only the FIRST record is finished; the second is still in progress
    return [j1.id, j2.id]
case("D two records share payload id, ack 1st",
     lambda t: external(t, [{"id": "dup", "n": 0}, {"id": "dup", "n": 1}]), dup, 1)
