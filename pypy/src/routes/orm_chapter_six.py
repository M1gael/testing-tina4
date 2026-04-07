# testing orm chapter six features
from tina4_python.core.router import get, post, put, delete as delete_route, noauth
from src.orm.note import Note
from src.orm.author import Author
from src.orm.blog_post import BlogPost
from src.orm.task import Task
from src.orm.product import Product
from tina4_python.crud import AutoCrud
from tina4_python.orm.model import snake_to_camel, camel_to_snake

# testing Section 9: Auto-CRUD
AutoCrud.register(Note)
AutoCrud.register(Author)
AutoCrud.register(BlogPost)

@get("/chapter6/init")
@noauth()
async def init_orm(request, response):
    # testing Section 3: create_table
    results = {}
    try:
        results["note"] = Note.create_table()
        results["author"] = Author.create_table()
        results["blog_post"] = BlogPost.create_table()
        results["task"] = Task.create_table()
        results["product"] = Product.create_table()
        return response.json({"status": "success", "results": results})
    except Exception as e:
        import traceback
        return response.json({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }, 500)

@post("/chapter6/notes")
@noauth()
async def create_note(request, response):
    # testing Section 4.1: save (create)
    note = Note()
    note.title = request.body.get("title", "Untitled")
    note.content = request.body.get("content", "")
    note.save()
    return response.json(note.to_dict(), 201)

@get("/chapter6/notes/{id:int}")
@noauth()
async def get_note(id, request, response):
    # testing Section 4.2: find
    note = Note.find(id)
    if not note:
        return response.json({"error": "Note not found"}, 404)
    return response.json(note.to_dict())

@put("/chapter6/notes/{id:int}")
@noauth()
async def update_note(id, request, response):
    # testing Section 4.1: save (update)
    note = Note.find(id)
    if not note:
        return response.json({"error": "Note not found"}, 404)
    
    note.title = request.body.get("title", note.title)
    note.content = request.body.get("content", note.content)
    note.save()
    return response.json(note.to_dict())

@delete_route("/chapter6/notes/{id:int}")
@noauth()
async def delete_note(id, request, response):
    # testing Section 4.3: delete
    note = Note.find(id)
    if not note:
        return response.json({"error": "Note not found"}, 404)
    note.delete()
    return response.json(None, 204)

@get("/chapter6/notes")
@noauth()
async def list_notes(request, response):
    # testing Section 4.4: all
    notes, count = Note.all()
    return response.json({"data": [n.to_dict() for n in notes], "count": count})

@get("/chapter6/authors/{id:int}")
@noauth()
async def get_author(id, request, response):
    # testing Section 6: Relationships - has_many
    author = Author.find(id)
    if not author:
        return response.json({"error": "Author not found"}, 404)
    
    posts = author.has_many(BlogPost, "author_id")
    data = author.to_dict()
    data["posts"] = [post.to_dict() for post in posts]
    return response.json(data)

@get("/chapter6/posts/{id:int}")
@noauth()
async def get_post(id, request, response):
    # testing Section 6: Relationships - belongs_to
    post = BlogPost.find(id)
    if not post:
        return response.json({"error": "Post not found"}, 404)
    
    author = post.belongs_to(Author, "author_id")
    data = post.to_dict()
    data["author"] = author.to_dict() if author else None
    return response.json(data)

@post("/chapter6/products")
@noauth()
async def create_product(request, response):
    # testing Section 11: Input Validation
    product = Product()
    product.name = request.body.get("name")
    product.sku = request.body.get("sku")
    product.price = request.body.get("price")
    product.category = request.body.get("category")

    errors = product.validate()
    if errors:
        return response.json({"errors": errors}, 400)

    product.save()
    return response.json({"product": product.to_dict()}, 201)

@get("/chapter6/case-conversion")
@noauth()
async def test_case_conversion(request, response):
    # testing Section 2.4: case conversion utilities
    return response.json({
        "snake_to_camel": snake_to_camel("first_name"),
        "camel_to_snake": camel_to_snake("firstName")
    })

@get("/chapter6/authors-eager")
@noauth()
async def authors_eager(request, response):
    # testing Section 7: Eager Loading
    authors, count = Author.all(include=["posts"])
    data = []
    for author in authors:
        author_dict = author.to_dict()
        author_dict["posts"] = [p.to_dict() for p in author.posts]
        data.append(author_dict)
    return response.json({"authors": data})

@delete_route("/chapter6/tasks/{id:int}")
@noauth()
async def delete_task(id, request, response):
    # testing Section 8: Soft Delete
    task = Task.find(id)
    if not task:
        return response.json({"error": "Task not found"}, 404)
    task.delete() # should set deleted_at
    return response.json({"message": "Task soft-deleted", "task": task.to_dict()})

@post("/chapter6/tasks/{id:int}/restore")
@noauth()
async def restore_task(id, request, response):
    # testing Section 8: Restore
    tasks, count = Task.with_trashed("id = ?", [id])
    task = tasks[0] if tasks else None
    if not task:
        return response.json({"error": "Task not found"}, 404)
    task.restore()
    return response.json({"message": "Task restored", "task": task.to_dict()})

@get("/chapter6/posts/published")
@noauth()
async def published_posts(request, response):
    # testing Section 10: Scopes
    posts, count = BlogPost.published()
    return response.json({"posts": [p.to_dict() for p in posts]})
