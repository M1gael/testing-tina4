import datetime
from functools import wraps

import jwt
from flask import Flask, jsonify, render_template, request
from flask_smorest import Api, Blueprint
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy.orm import DeclarativeBase

SECRET = "demo-secret"


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["API_TITLE"] = "Bookmarks"
app.config["API_VERSION"] = "1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
db = SQLAlchemy(app, model_class=Base)
api = Api(app)


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "url": self.url}


class BookmarkSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    url = fields.Str()


class LoginSchema(Schema):
    username = fields.Str()
    password = fields.Str()


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            jwt.decode(header[7:], SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


blp = Blueprint("bookmarks", __name__, url_prefix="/api")


@blp.route("/bookmarks", methods=["GET"])
@blp.response(200, BookmarkSchema(many=True))
def list_bookmarks():
    return Bookmark.query.all()


@blp.route("/bookmarks", methods=["POST"])
@blp.arguments(BookmarkSchema)
@blp.response(201, BookmarkSchema)
@token_required
def add_bookmark(data):
    if not data.get("url"):
        return jsonify({"error": "url is required"}), 400
    bookmark = Bookmark(title=data.get("title", ""), url=data["url"])
    db.session.add(bookmark)
    db.session.commit()
    return bookmark


@blp.route("/login", methods=["POST"])
@blp.arguments(LoginSchema)
def login(data):
    if data.get("username") != "demo" or data.get("password") != "demo":
        return jsonify({"error": "invalid credentials"}), 401
    payload = {
        "username": "demo",
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
    }
    return jsonify({"token": jwt.encode(payload, SECRET, algorithm="HS256")})


api.register_blueprint(blp)


@app.get("/bookmarks")
def bookmarks_page():
    return render_template("bookmarks.html", bookmarks=Bookmark.query.all())


with app.app_context():
    db.create_all()
    if not Bookmark.query.first():
        db.session.add(Bookmark(title="Tina4", url="https://tina4.com"))
        db.session.commit()
