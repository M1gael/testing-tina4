# ch06 section 8 — "Soft Delete" (fields verbatim, 06-orm.md:762-774).
# ch06 section 9 — "Auto-CRUD": `auto_crud = True` generates the five REST
# endpoints at /api/tasks (the documented one-line flag, 06-orm.md:838-845).
# Task has no custom routes, so it's a clean auto-CRUD target — and its
# soft_delete lets us check the "DELETE respects soft delete" claim (S9:939).
from tina4_python.orm import ORM, IntegerField, StringField, BooleanField

class Task(ORM):
    table_name = "tasks"
    soft_delete = True  # Enable soft delete
    auto_crud = True    # S9 — generates /api/tasks REST endpoints automatically

    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True)
    completed = BooleanField(default=False)
    is_deleted = IntegerField(default=0)  # Required for soft delete (0 = active, 1 = deleted)
    created_at = StringField()
