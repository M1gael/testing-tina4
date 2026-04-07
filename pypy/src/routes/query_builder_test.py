# testing query builder features
from tina4_python.core.router import get, noauth
from tina4_python.query_builder import QueryBuilder
from tina4_python.database import Database

@get("/chapter7/init")
@noauth()
async def init_qb(request, response):
    # testing query builder prerequisite: tables and data
    db = Database()
    try:
        # creating tables manually for join tests if they don't exist
        db.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, category_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        
        # dummy data
        db.execute("DELETE FROM categories")
        db.execute("DELETE FROM products")
        
        cat1 = db.execute("INSERT INTO categories (name) VALUES (?)", ["Electronics"]).last_id
        cat2 = db.execute("INSERT INTO categories (name) VALUES (?)", ["Outdoor"]).last_id
        
        db.execute("INSERT INTO products (name, price, category_id) VALUES (?, ?, ?)", ["Smartphone", 699.99, cat1])
        db.execute("INSERT INTO products (name, price, category_id) VALUES (?, ?, ?)", ["Laptop", 1200.00, cat1])
        db.execute("INSERT INTO products (name, price, category_id) VALUES (?, ?, ?)", ["Tent", 150.00, cat2])
        
        return response.json({"status": "success", "message": "Tables and data initialized"})
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)

@get("/chapter7/test-basics")
@noauth()
async def test_basics(request, response):
    # testing Section 1, 2, 3: from_table, select, where
    db = Database()
    qb = QueryBuilder.from_table("products", db) \
        .select("name", "price") \
        .where("price > ?", [500])
    
    sql = qb.to_sql()
    result = qb.get() # tests execution
    
    return response.json({
        "sql": sql,
        "results": result.to_list()
    })

@get("/chapter7/test-joins")
@noauth()
async def test_joins(request, response):
    # testing Section 4: join and left_join
    db = Database()
    qb = QueryBuilder.from_table("products", db) \
        .select("products.name", "categories.name as category") \
        .join("categories", "categories.id = products.category_id")
    
    sql = qb.to_sql()
    result = qb.get()
    
    return response.json({
        "sql": sql,
        "results": result.to_list()
    })

@get("/chapter7/test-aggregation")
@noauth()
async def test_aggregation(request, response):
    # testing Section 5: group_by and having
    db = Database()
    qb = QueryBuilder.from_table("products", db) \
        .select("category_id", "COUNT(*) as count") \
        .group_by("category_id") \
        .having("COUNT(*) >= ?", [1])
    
    sql = qb.to_sql()
    result = qb.get()
    
    return response.json({
        "sql": sql,
        "results": result.to_list()
    })

@get("/chapter7/test-execution")
@noauth()
async def test_execution(request, response):
    # testing Section 9: first, count, exists
    db = Database()
    qb = QueryBuilder.from_table("products", db).where("name = ?", ["Smartphone"])
    
    return response.json({
        "first": qb.first(),
        "count": qb.count(),
        "exists": qb.exists()
    })

@get("/chapter7/test-mongo")
@noauth()
async def test_mongo(request, response):
    # testing NoSQL: MongoDB Queries (Section 11/12)
    qb = QueryBuilder.from_table("users") \
        .select("name", "email") \
        .where("age > ?", [25]) \
        .where("status = ?", ["active"]) \
        .order_by("name ASC") \
        .limit(10, 5)
    
    return response.json(qb.to_mongo())
