# ch06 section 6 — "Relationships" / has_many
# VERBATIM from the chapter (Create src/orm/author.py, lines 536-547).
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField

class Author(ORM):
    table_name = "authors"

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    email = StringField(required=True)
    bio = StringField(default="")
    created_at = DateTimeField()
