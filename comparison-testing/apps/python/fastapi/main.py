import datetime

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

SECRET = "demo-secret"

engine = create_engine("sqlite:///app.db")
templates = Jinja2Templates(directory="templates")
app = FastAPI(title="Bookmarks")
bearer = HTTPBearer(auto_error=False)


class Base(DeclarativeBase):
    pass


class Bookmark(Base):
    __tablename__ = "bookmark"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "url": self.url}


class BookmarkIn(BaseModel):
    title: str = ""
    url: str = ""


class Login(BaseModel):
    username: str = ""
    password: str = ""


def require_token(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if creds is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/api/bookmarks")
async def list_bookmarks():
    with Session(engine) as session:
        return [b.to_dict() for b in session.scalars(select(Bookmark)).all()]


@app.post("/api/bookmarks", status_code=201, dependencies=[Depends(require_token)])
async def add_bookmark(data: BookmarkIn):
    if not data.url:
        raise HTTPException(status_code=400, detail="url is required")
    with Session(engine) as session:
        bookmark = Bookmark(title=data.title, url=data.url)
        session.add(bookmark)
        session.commit()
        return bookmark.to_dict()


@app.post("/api/login")
async def login(data: Login):
    if data.username != "demo" or data.password != "demo":
        raise HTTPException(status_code=401, detail="invalid credentials")
    payload = {
        "username": "demo",
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
    }
    return {"token": jwt.encode(payload, SECRET, algorithm="HS256")}


@app.get("/bookmarks")
async def bookmarks_page(request: Request):
    with Session(engine) as session:
        rows = session.scalars(select(Bookmark)).all()
        return templates.TemplateResponse(request, "bookmarks.html", {"bookmarks": rows})


Base.metadata.create_all(engine)
with Session(engine) as session:
    if not session.scalars(select(Bookmark)).first():
        session.add(Bookmark(title="Tina4", url="https://tina4.com"))
        session.commit()
