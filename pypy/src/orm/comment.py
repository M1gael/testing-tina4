# testing orm comment model
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField, ForeignKeyField

class Comment(ORM):
    table_name = "comments"

    id = IntegerField(auto_increment=True)
    post_id = ForeignKeyField("posts.id", required=True)
    author_name = StringField(required=True)
    author_email = StringField(required=True)
    body = StringField(required=True, min_length=5)
    created_at = DateTimeField(auto_now_add=True)
