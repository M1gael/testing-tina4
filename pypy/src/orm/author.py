# ch06 section 6 — "Relationships" / has_many (model fields verbatim, lines 536-547).
# ch06 section 7 — "Declarative Relationships with Descriptors" adds the `posts`
# descriptor to this model (06-orm.md:684).
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField
from tina4_python.orm import has_many

class Author(ORM):
    table_name = "authors"

    id = IntegerField(primary_key=True, auto_increment=True)
    name = StringField(required=True)
    email = StringField(required=True)
    bio = StringField(default="")
    created_at = DateTimeField()

    # S7 descriptor — declared once on the class
    posts = has_many("BlogPost", foreign_key="author_id")
