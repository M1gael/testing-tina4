# ch06 section 8 — "Soft Delete"
# VERBATIM from the chapter (06-orm.md:762-774).
from tina4_python.orm import ORM, IntegerField, StringField, BooleanField

class Task(ORM):
    table_name = "tasks"
    soft_delete = True  # Enable soft delete

    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    completed = BooleanField(default=False)
    is_deleted = IntegerField(default=0)  # Required for soft delete (0 = active, 1 = deleted)
    created_at = StringField()
