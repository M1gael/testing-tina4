from tina4_python.core.router import get, post

from src.orm.bookmark import Bookmark


@get("/api/bookmarks")
async def list_bookmarks(request, response):
    return response.json([b.to_dict() for b in Bookmark.all()])


@post("/api/bookmarks")
async def add_bookmark(request, response):
    data = request.body or {}
    if not data.get("url"):
        return response.json({"error": "url is required"}, 400)
    bookmark = Bookmark(data)
    bookmark.save()
    return response.json(bookmark.to_dict(), 201)


@get("/bookmarks")
async def bookmarks_page(request, response):
    return response.render("bookmarks.html", {"bookmarks": Bookmark.all()})
