# Probe — covers BH-47 (#47). The lazy-import ImportError for the PostgreSQL driver
# must recommend the `tina4-python[<extra>]` extras form, not just a bare pip install.
# Fixed v3.13.6; OUR-verified on 3.13.39 (2026-06-22) by reading the shipped adapter
# source — psycopg2 is installed in this venv, so the ImportError cannot be triggered
# at runtime. Flips red if the extras-form hint is dropped from the raised message.
import tina4_python.database.postgres as pg


def test_postgres_importerror_recommends_extras_form():
    src = open(pg.__file__, encoding="utf-8").read()
    assert "tina4-python[postgres]" in src
    assert "tina4-python[all-db]" in src
