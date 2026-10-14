# Stock tina4-python v3: AutoCrud + Crud.to_crud over a 3-row sqlite table.
import os
from tina4_python.database import Database
from tina4_python.orm.model import ORM, bind_database
from tina4_python.orm.fields import IntegerField, StringField
from tina4_python.crud import AutoCrud, Crud
from tina4_python.core.router import get, noauth
from tina4_python import run

if os.path.exists("people.db"):
    os.remove("people.db")
db = Database("sqlite:///people.db")
bind_database(db)
db.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)")
for n, a in (("Ann", 30), ("O'Brien", 40), ("Zed", 25)):
    db.insert("people", {"name": n, "age": a})
db.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT)")
db.insert("secrets", {"id": 1, "token": "TOPSECRET"})
db.commit()

class Person(ORM):
    table_name = "people"
    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField()
    age = IntegerField()

AutoCrud.register(Person, public=True)

@noauth()
@get("/grid")
async def grid(request, response):
    return response(Crud.to_crud(request, model=Person))

@noauth()
@get("/gridsql")
async def gridsql(request, response):
    return response(Crud.to_crud(request, model=Person, sql="SELECT id, name, age FROM people"))

if __name__ == "__main__":
    run(port=int(os.environ.get("PORT", "7461")), no_browser=True, no_reload=True)
