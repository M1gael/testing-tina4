# testing orm soft delete model
from tina4_python.orm import ORM, IntegerField, StringField, BooleanField, DateTimeField

class Task(ORM):
    table_name = "tasks"
    soft_delete = True  # Enable soft delete

    id = IntegerField(auto_increment=True)
    title = StringField(required=True)
    completed = BooleanField(default=False)
    deleted_at = DateTimeField()  # Required for soft delete
    created_at = DateTimeField(auto_now_add=True)
