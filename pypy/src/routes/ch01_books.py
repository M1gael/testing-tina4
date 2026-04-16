# chapter 1: worked example a complete route file
from tina4_python.core.router import get, post

# in-memory data store
books = [
    {"id": 1, "title": "Dune", "author": "Frank Herbert", "year": 1965},
    {"id": 2, "title": "Neuromancer", "author": "William Gibson", "year": 1984},
    {"id": 3, "title": "Snow Crash", "author": "Neal Stephenson", "year": 1992}
]


@get("/api/books")
async def list_books(request, response):
    """list all books. supports ?author= filter and ?sort=year."""
    author = request.params.get("author", "")
    sort_by = request.params.get("sort", "")

    result = books

    # filter by author if the query param is present
    if author:
        result = [b for b in result if author.lower() in b["author"].lower()]

    # sort by year if requested
    if sort_by == "year":
        result = sorted(result, key=lambda b: b["year"])

    return response.json({"books": result, "count": len(result)})


@get("/api/books/{id:int}")
async def get_book(id, request, response):
    """get a single book by id. returns 404 if not found."""
    book = next((b for b in books if b["id"] == id), None)

    if book is None:
        return response.json({"error": f"Book with id {id} not found"}, 404)

    return response.json(book)
