# chapter 2: path parameters
from tina4_python.core.router import get

@get("/users/{id}/posts/{post_id}")
async def user_post(id, post_id, request, response):
    return response.json({
        "user_id": id,
        "post_id": post_id
    })
