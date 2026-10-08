"""tina4-python: is a pgsql:// URL accepted like postgres://, or refused by scheme?

Every URL points at port 1, where nothing listens: an accepted scheme fails at the
connect, a refused one fails before it. Run with the tree's own interpreter:
    <tina4-python checkout>/.venv/bin/python prove.py
"""
import subprocess
from pathlib import Path

import tina4_python
from tina4_python.database import Database
from tina4_python.database.database_url import DatabaseUrl

tree = Path(tina4_python.__file__).resolve().parent.parent
rev = subprocess.run(["git", "-C", str(tree), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
version = next(l for l in (tree / "pyproject.toml").read_text().splitlines() if l.startswith("version"))
print(f"tree: {rev}, {version}")
for url in ("pgsql://127.0.0.1:1/x", "postgres://127.0.0.1:1/x", "postgresql://127.0.0.1:1/x"):
    try:
        engine = DatabaseUrl(url).engine
    except Exception as exc:
        engine = f"refused ({type(exc).__name__})"
    try:
        Database(url)
        outcome = "connected (unexpected)"
    except Exception as exc:
        outcome = f"{type(exc).__name__}: {str(exc)[:90]}"
    print(f"{url}: DatabaseUrl engine {engine}; Database() -> {outcome}")
