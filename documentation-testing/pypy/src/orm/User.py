# ch18 S7 supporting model — User (PY-18-12 / PY-18-11 scaffold).
# Chapter references User in S7 with no model definition; this is the minimal
# Ch06-shape implementation so S7 test snippets can run.

from tina4_python.orm import ORM, IntegerField, StringField


class User(ORM):
    table_name = "users"

    id    = IntegerField(primary_key=True, auto_increment=True)
    name  = StringField()
    email = StringField()
