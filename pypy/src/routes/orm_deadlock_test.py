from tina4_python import orm_bind, ORM, IntegerField, StringField, noauth, get, Database
import os

# testing orm deadlock (py-0506-03)

@orm_bind
class TestDeadlock(ORM):
    id = IntegerField(primary_key=True)
    name = StringField()

@get("/test-orm-init")
@noauth()
async def init_orm(request, response):
    try:
        db = Database()
        return response.json({
            "type": str(type(TestDeadlock)),
            "methods": str(dir(TestDeadlock))
        })
    except Exception as e:
        return response.json({"error": str(e)}, 500)
