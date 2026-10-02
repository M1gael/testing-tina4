from tina4_python.core.router import get
import tina4_python.session


@get("/where")
async def where(request, response):
    return response(tina4_python.session.__file__)


@get("/plain")
async def plain(request, response):  # never touches the session
    return response("plain")


@get("/read")
async def read(request, response):
    return response("user=" + (request.session.get("user") or "-"))


@get("/write")
async def write(request, response):
    request.session.set("user", "alice")
    return response("wrote")


@get("/login")
async def login(request, response):  # regenerate, then set
    request.session.regenerate()
    request.session.set("user", "alice")
    return response("logged in")


@get("/flash-set")
async def flash_set(request, response):
    request.session.flash("notice", "saved")
    return response("flashed")


@get("/flash-get")
async def flash_get(request, response):
    return response("flash=" + (request.session.get_flash("notice") or "-"))
