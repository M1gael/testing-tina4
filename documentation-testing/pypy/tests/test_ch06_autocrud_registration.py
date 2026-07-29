# Verbatim-impl test — Chapter 6 ORM, S9 "Auto-CRUD": the registration surfaces the
# main S9 test (test_ch06_autocrud.py) does not exercise:
#   - the auto_crud=True flag auto-registering on class load, via the verbatim Product
#     model (06-orm.md:851-861) using Field(float, default=0.0);
#   - AutoCrud.register(Note) with the DEFAULT prefix -> /api/notes, and the
#     "prefix derives from the table name" claim (06-orm.md:865-891);
#   - AutoCrud.discover("src/orm", prefix="/api") scanning + registering every model
#     (06-orm.md:893-901).
# Each snippet mutates AutoCrud's GLOBAL route table — a global /api/notes auto-CRUD
# registration would shadow the custom routes the ch06_routes/note_crud tests rely on
# (PY-06-18) — so each runs in an isolated subprocess and asserts on its output.
import os
import subprocess
import sys

PYPY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {**os.environ, "TINA4_DATABASE_URL": os.environ.get(
    "TINA4_DATABASE_URL", "postgresql://postgres:tina4test@localhost:5432/tina4testingdb")}


def _run(snippet):
    r = subprocess.run([sys.executable, "-c", snippet], cwd=PYPY, env=ENV,
                       capture_output=True, text=True)
    assert r.returncode == 0, f"subprocess failed:\n{r.stderr}"
    return r.stdout + "\n" + r.stderr


# auto_crud=True on class load auto-registers (06-orm.md:837-861, verbatim Product)
def test_auto_crud_flag_registers_on_load():
    out = _run(
        "from tina4_python.orm import ORM, Field, IntegerField, StringField\n"
        "class Product(ORM):\n"
        "    table_name = 'products'\n"
        "    auto_crud  = True\n"
        "    id    = IntegerField(primary_key=True, auto_increment=True)\n"
        "    name  = StringField(required=True)\n"
        "    price = Field(float, default=0.0)\n"
        "from tina4_python.crud import AutoCrud\n"
        "print('PRODUCTS_REGISTERED', 'products' in AutoCrud.models())\n"
    )
    assert "PRODUCTS_REGISTERED True" in out


# AutoCrud.register(Note) default prefix -> /api/notes (06-orm.md:865-891)
def test_register_default_prefix_derives_from_table():
    out = _run(
        "from tina4_python.crud import AutoCrud\n"
        "from src.orm.note import Note\n"
        "AutoCrud.register(Note)\n"
        "print('NOTES_REGISTERED', 'notes' in AutoCrud.models())\n"
    )
    assert "NOTES_REGISTERED True" in out
    # the framework logs the derived path; the table name 'notes' -> '/api/notes'
    assert "/api/notes" in out


# AutoCrud.discover('src/orm', prefix='/api') registers every ORM model (06-orm.md:893-901)
def test_discover_registers_src_orm_models():
    out = _run(
        "from tina4_python.crud import AutoCrud\n"
        "AutoCrud.discover('src/orm', prefix='/api')\n"
        "import json\n"
        "print('MODELS', json.dumps(sorted(AutoCrud.models().keys())))\n"
    )
    # the ORM subclasses defined under src/orm all get registered
    for table in ("notes", "tasks", "authors", "products"):
        assert f'"{table}"' in out, f"{table} not registered by discover(); got: {out}"
