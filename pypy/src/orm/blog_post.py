# testing orm blog post model
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField, ForeignKeyField

class BlogPost(ORM):
    table_name = "posts"

    id = IntegerField(auto_increment=True)
    author_id = ForeignKeyField("authors.id", required=True)
    title = StringField(required=True, max_length=300)
    slug = StringField(required=True)
    content = StringField(default="")
    status = StringField(default="draft", choices=["draft", "published", "archived"])
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    @classmethod
    def published(cls):
        return cls.where("status = ?", ["published"])
