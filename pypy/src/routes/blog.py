# testing chapter 6 orm (partially untestable via http due to splite table creation constraints and locks)
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
        return response.json({"errors": errors}, 400)

    author.save()
    return response.json({"author": author.to_dict()}, 201)


@get("/api/authors/{id:int}")
async def get_author(request, response):
    author = Author.find(request.params["id"])

    if author is None:
        return response.json({"error": "Author not found"}, 404)

    posts, count = BlogPost.where("author_id = ?", [author.id])

    data = author.to_dict()
    data["posts"] = [p.to_dict() for p in posts]

    return response.json(data)


@post("/api/posts")
async def create_post(request, response):
    body = request.body

    # Verify author exists
    author = Author.find(body.get("author_id"))
    if author is None:
        return response.json({"error": "Author not found"}, 404)

    blog_post = BlogPost()
    blog_post.author_id = body["author_id"]
    blog_post.title = body.get("title")
    blog_post.slug = body.get("slug")
    blog_post.content = body.get("content", "")
    blog_post.status = body.get("status", "draft")

    errors = blog_post.validate()
    if errors:
        return response.json({"errors": errors}, 400)

    blog_post.save()
    return response.json({"post": blog_post.to_dict()}, 201)


@get("/api/posts")
async def list_posts(request, response):
    posts = BlogPost.published()
    data = []

    for p in posts:
        post_dict = p.to_dict()
        author = p.belongs_to(Author, "author_id")
        post_dict["author"] = author.to_dict(include=["id", "name"]) if author else None
        data.append(post_dict)

    return response.json({"posts": data, "count": len(data)})


@get("/api/posts/{id:int}")
async def get_post(id, request, response):
    blog_post = BlogPost.find(id)


    if blog_post is None:
        return response.json({"error": "Post not found"}, 404)

    author = blog_post.belongs_to(Author, "author_id")
    comments = blog_post.has_many(Comment, "post_id")

    data = blog_post.to_dict()
    data["author"] = author.to_dict() if author else None
    data["comments"] = [c.to_dict() for c in comments]
    data["comment_count"] = len(comments)

    return response.json(data)


@post("/api/posts/{id:int}/comments")
async def add_comment(id, request, response):
    blog_post = BlogPost.find(id)


    if blog_post is None:
        return response.json({"error": "Post not found"}, 404)

    comment = Comment()
    comment.post_id = request.params["id"]
    comment.author_name = request.body.get("author_name")
    comment.author_email = request.body.get("author_email")
    comment.body = request.body.get("body")

    errors = comment.validate()
    if errors:
        return response.json({"errors": errors}, 400)

    comment.save()
    return response.json({"comment": comment.to_dict()}, 201)
