# ch06 section 6 — "Relationships" / has_many (model fields, lines 536-547).
# ch06 section 7 — "Declarative Relationships with Descriptors" adds the `posts`
# descriptor to this model (06-orm.md:684).
# ch06 section 14 — "Solution" redefines Author (06-orm.md:1116-1124) and INTRODUCES
# `min_length=2` on name; this file is aligned to the later (S14) definition.
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField
from tina4_python.orm import has_many

class Author(ORM):
    table_name = "authors"

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True, min_length=2)  # S14 (06-orm.md:1120)
    email = StringField(required=True)
    bio = StringField(default="")
    created_at = DateTimeField()

    # S7 descriptor — declared once on the class
    posts = has_many("BlogPost", foreign_key="author_id")
