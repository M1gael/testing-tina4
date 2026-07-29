# ch06 section 14 — "Solution" (Build a Blog), Comment model — VERBATIM
# (06-orm.md:1150-1162). S7 references this model before it is defined (PY-06-12);
# it first appears here in S14.
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField

class Comment(ORM):
    table_name = "comments"

    id = IntegerField(primary_key=True, auto_increment=True)
    post_id = IntegerField(required=True)
    author_name = StringField(required=True)
    author_email = StringField(required=True)
    body = StringField(required=True, min_length=5)
    created_at = DateTimeField()
