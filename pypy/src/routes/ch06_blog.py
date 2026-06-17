# ch06 section 6 — "Relationships" (route handlers)
# VERBATIM handler bodies from the chapter: get_author / has_many (570-582),
# get_post / belongs_to (613-625). S6 shows no import lines for these two
# snippets; the imports below are the ones the handlers require (get +
# Author + BlogPost), following the S4 import pattern.
from tina4_python.core.router import get
from src.orm.author import Author
from src.orm.blog_post import BlogPost


@get("/api/authors/{id:int}")
async def get_author(id, request, response):
    author = Author.find_by_id(id)

    if author is None:
        return response({"error": "Author not found"}, 404)

    posts = author.has_many(BlogPost, "author_id")

    data = author.to_dict()
    data["posts"] = [post.to_dict() for post in posts]

    return response(data)


@get("/api/posts/{id:int}")
async def get_post(id, request, response):
    post = BlogPost.find_by_id(id)

    if post is None:
        return response({"error": "Post not found"}, 404)

    author = post.belongs_to(Author, "author_id")

    data = post.to_dict()
    data["author"] = author.to_dict() if author else None

    return response(data)
