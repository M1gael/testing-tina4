# ch06 section 11 — "Scopes" (route handlers). VERBATIM from the chapter
# (06-orm.md:1008-1017). S11 shows no import lines for these snippets; the
# imports below follow the S6 route pattern (get + BlogPost).
from tina4_python.core.router import get
from src.orm.blog_post import BlogPost


@get("/api/posts/published")
async def published_posts(request, response):
    posts = BlogPost.published()
    return response({"posts": [p.to_dict() for p in posts]})


@get("/api/posts/recent")
async def recent_posts(request, response):
    days = int(request.params.get("days", 7))
    posts = BlogPost.recent(days)
    return response({"posts": [p.to_dict() for p in posts]})
