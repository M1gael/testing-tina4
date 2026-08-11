from tina4_python.orm import ORM, IntegerField, StringField


class Bookmark(ORM):
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField()
    url = StringField()
