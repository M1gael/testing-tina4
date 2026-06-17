# ch06 section 6 — Relationships (has_many / has_one / belongs_to)
#
# See test_ch06_note_crud.py header for the DB-connection reminder.
#
# Patched pass: the chapter (S6) defines Author + BlogPost and uses
# has_many/belongs_to with NO create_table or migration shown for either model
# (S3 shows create_table only for Note). The verbatim run hits UndefinedTable
# (logged PY-06-02); this file PATCHES in the table creation so the documented
# S6 relationship API itself — has_many / belongs_to — can be exercised.
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none
from src.orm.author import Author
from src.orm.blog_post import BlogPost


class RelationshipsTest(Test):

    # ============================== PATCHES ==============================
    # PATCH [PY-06-02]: S6 defines Author + BlogPost and queries them with no
    # create_table/migration shown (S3 shows create_table only for Note). Without
    # this, every save raises UndefinedTable: relation "authors"/"posts" does not
    # exist. Create the tables so the relationship API can be exercised.
    def set_up(self):
        Author.create_table()
        BlogPost.create_table()
    # ============================ END PATCHES ============================

    def test_has_many(self):
        author = Author()
        author.name = "Alice"
        author.email = "alice@example.com"
        author.bio = "Tech writer"
        author.save()

        p1 = BlogPost()
        p1.author_id = author.id
        p1.title = "Getting Started with Tina4"
        p1.slug = "getting-started"
        p1.status = "published"
        p1.save()

        posts = author.has_many(BlogPost, "author_id")
        assert_true(len(posts) >= 1, "author should have at least one post")

    def test_belongs_to(self):
        author = Author()
        author.name = "Bob"
        author.email = "bob@example.com"
        author.save()

        post = BlogPost()
        post.author_id = author.id
        post.title = "Advanced Routing"
        post.slug = "advanced-routing"
        post.save()

        loaded = BlogPost.find_by_id(post.id)
        owner = loaded.belongs_to(Author, "author_id")
        assert_not_none(owner, "post should resolve its author")
        assert_equal(owner.name, "Bob", "belongs_to should return the right author")
