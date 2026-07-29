# ch06 section 14 — "Solution" (Build a Blog), routes — VERBATIM (06-orm.md:1166-1277).
#
# NOTE (workspace artifact, not a doc divergence): get_author and get_post here
# register the SAME paths (GET /api/authors/{id:int}, GET /api/posts/{id:int}) as
# the S6 snippet file src/routes/ch06_blog.py. The router keeps the registry free
# of duplicates and the latest-loaded handler wins (router.py:358), so no crash;
# whichever file imports last serves those two paths. A reader doing only the
# S13/14 exercise would create just this file.
from tina4_python.core.router import get, post
from src.orm.author import Author
from src.orm.blog_post import BlogPost
from src.orm.comment import Comment


@post("/api/authors")
async def create_author(request, response):
    author = Author()
    author.name = request.body.get("name")
    author.email = request.body.get("email")
    author.bio = request.body.get("bio", "")

    errors = author.validate()
    if errors:
        return response({"errors": errors}, 400)

    author.save()
    return response({"author": author.to_dict()}, 201)


@get("/api/authors/{id:int}")
async def get_author(id, request, response):
    author = Author.find_by_id(id)

    if author is None:
        return response({"error": "Author not found"}, 404)

    posts = BlogPost.where("author_id = ?", [author.id])

    data = author.to_dict()
    data["posts"] = [p.to_dict() for p in posts]

    return response(data)


@post("/api/posts")
async def create_post(request, response):
    body = request.body

    # Verify author exists
    author = Author.find_by_id(body.get("author_id"))
    if author is None:
        return response({"error": "Author not found"}, 404)

    blog_post = BlogPost()
    blog_post.author_id = body["author_id"]
    blog_post.title = body.get("title")
    blog_post.slug = body.get("slug")
    blog_post.content = body.get("content", "")
    blog_post.status = body.get("status", "draft")

    errors = blog_post.validate()
    if errors:
        return response({"errors": errors}, 400)

    blog_post.save()
    return response({"post": blog_post.to_dict()}, 201)


@get("/api/posts")
async def list_posts(request, response):
    posts = BlogPost.published()
    data = []

    for p in posts:
        post_dict = p.to_dict()
        author = p.belongs_to(Author, "author_id")
        post_dict["author"] = author.to_dict() if author else None
        data.append(post_dict)

    return response({"posts": data, "count": len(data)})


@get("/api/posts/{id:int}")
async def get_post(id, request, response):
    blog_post = BlogPost.find_by_id(id)

    if blog_post is None:
        return response({"error": "Post not found"}, 404)

    author = blog_post.belongs_to(Author, "author_id")
    comments = blog_post.has_many(Comment, "post_id")

    data = blog_post.to_dict()
    data["author"] = author.to_dict() if author else None
    data["comments"] = [c.to_dict() for c in comments]
    data["comment_count"] = len(comments)

    return response(data)


@post("/api/posts/{id:int}/comments")
async def add_comment(id, request, response):
    blog_post = BlogPost.find_by_id(id)

    if blog_post is None:
        return response({"error": "Post not found"}, 404)

    comment = Comment()
    comment.post_id = id
    comment.author_name = request.body.get("author_name")
    comment.author_email = request.body.get("author_email")
    comment.body = request.body.get("body")

    errors = comment.validate()
    if errors:
        return response({"errors": errors}, 400)

    comment.save()
    return response({"comment": comment.to_dict()}, 201)
