# ch06 section 6 — "Relationships" / has_many (model fields verbatim, lines 549-565).
# ch06 section 7 — "Declarative Relationships with Descriptors" adds the `author`
# and `comments` descriptors (06-orm.md:695-697). NOTE: `comments` targets a
# `Comment` model that S7 references but never defines (PY-06-12); it stays inert
# (and the comments examples are blocked) until a Comment model exists.
from tina4_python.orm import ORM, IntegerField, StringField, DateTimeField
from tina4_python.orm import belongs_to, has_many

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

    # S7 descriptors
    author   = belongs_to("Author", foreign_key="author_id")
    comments = has_many("Comment", foreign_key="post_id")

    # S11 scopes (06-orm.md:989-1002) — verbatim. recent() uses SQLite
    # datetime('now', ?); on PostgreSQL it raises UndefinedFunction (PY-06-23).
    @classmethod
    def published(cls):
        return cls.where("status = ?", ["published"])

    @classmethod
    def drafts(cls):
        return cls.where("status = ?", ["draft"])

    @classmethod
    def recent(cls, days=7):
        return cls.where(
            "created_at > datetime('now', ?)",
            [f"-{days} days"]
        )
