import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="tina4test",
    dbname="tina4_bug46",
)
cur = conn.cursor()

cur.execute("SELECT version();")
print("PG version:", cur.fetchone()[0])

cur.execute("SELECT count(*) FROM gift_cards;")
print("Rows in gift_cards:", cur.fetchone()[0])

cur.execute(
    "SELECT id, created_by_email, amount, is_deleted FROM gift_cards LIMIT 5;"
)
print()
print("First 5 rows:")
for row in cur.fetchall():
    print(" ", row)

conn.close()
