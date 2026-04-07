from tina4_python.database.connection import Database
import os

# testing pagination slicing (v3.10.50)

def test_pagination():
    db = Database()
    # ensure table exists
    db.execute("CREATE TABLE IF NOT EXISTS test_pag_v50 (id INTEGER PRIMARY KEY, title TEXT)")
    db.execute("DELETE FROM test_pag_v50")
    # insert 50 records
    for i in range(1, 51):
        db.execute("INSERT INTO test_pag_v50 (title) VALUES (?)", [f"Record {i}"])
    
    # fetch all
    res = db.fetch("SELECT * FROM test_pag_v50 ORDER BY id ASC")
    
    # paginate with page 2, per_page 10
    paginated = res.to_paginate(page=2, per_page=10)
    
    print(f"Page: {paginated.get('page')}")
    print(f"Per Page: {paginated.get('per_page')}")
    print(f"Data length: {len(paginated.get('data', []))}")
    if paginated.get('data'):
        print(f"First record in data: {paginated['data'][0]}")

if __name__ == "__main__":
    test_pagination()
