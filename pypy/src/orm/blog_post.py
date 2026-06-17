# ch06 section 6 — "Relationships" / has_many
# VERBATIM from the chapter (Create src/orm/blog_post.py, lines 549-565).
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField

class BlogPost(ORM):
    table_name = "posts"

    id = IntegerField(primary_key=True, auto_increment=True)
    author_id = IntegerField(required=True)
    title = StringField(required=True, max_length=300)
    slug = StringField(required=True)
    content = StringField(default="")
    status = StringField(default="draft", choices=["draft", "published", "archived"])
    created_at = DateTimeField()
    updated_at = DateTimeField()
