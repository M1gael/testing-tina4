from tina4_python.database.connection import Database
import os

# testing column_info (v3.10.50)

def test_column_info():
    db = Database()
    # ensure table exists
    db.execute("CREATE TABLE IF NOT EXISTS test_cols_v50 (id INTEGER PRIMARY KEY, title TEXT, price REAL)")
    db.execute("DELETE FROM test_cols_v50")
    db.execute("INSERT INTO test_cols_v50 (title, price) VALUES (?, ?)", ["Test", 10.99])
    
    # fetch 
    res = db.fetch("SELECT * FROM test_cols_v50")
    
    # get column info
    cols = res.column_info()
    
    print(f"Column Info: {cols}")

if __name__ == "__main__":
    test_column_info()
