"""Minimal psycopg2 example against the local tina4testingdb PostgreSQL fixture.

Run: uv run python tests/hello_pg.py
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="tina4test",
    dbname="tina4testingdb",
)
cur = conn.cursor()

cur.execute("SELECT version();")
print("PG version:", cur.fetchone()[0])

cur.execute("SELECT count(*) FROM items;")
print("Rows in items:", cur.fetchone()[0])

cur.execute("SELECT id, name, created_at FROM items LIMIT 5;")
print()
print("First 5 rows:")
for row in cur.fetchall():
    print(" ", row)

conn.close()
