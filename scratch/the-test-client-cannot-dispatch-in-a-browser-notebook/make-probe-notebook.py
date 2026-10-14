import nbformat as nbf
C = []
C.append("%pip install tina4-python==3.13.150")
C.append("""import sys, os, tina4_python
print('PY', sys.version.split()[0], 'T4', tina4_python.__version__, 'CWD', os.getcwd(), sorted(os.listdir('.')))""")
C.append("""import sqlite3
for path in ['data/plain.db', '/tmp/plain.db']:
    try:
        c = sqlite3.connect(path); c.execute('create table if not exists t(x)'); c.commit(); print('PLAIN', path, 'ok')
    except Exception as e:
        print('PLAIN', path, type(e).__name__, e)""")
C.append("""from tina4_python.database import Database
for url in ['sqlite:///data/t4.db', 'sqlite:////tmp/t4.db', 'sqlite:///:memory:']:
    try:
        d = Database(url); d.execute('create table if not exists t(x int)'); print('T4DB', url, 'ok')
    except Exception as e:
        print('T4DB', url, type(e).__name__, e)""")
C.append("""import csv
from tina4_python.orm import ORM, bind_database, IntegerField, StringField
bind_database(Database('sqlite:///:memory:'))
class Book(ORM):
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField()
    pages = IntegerField()
Book.create_table()
for row in csv.DictReader(open('data/books.csv')):
    Book.create(row)
print('ORM', [b.to_dict() for b in Book.all()])""")
C.append("""from tina4_python.frond import Frond
from IPython.display import HTML
html = Frond().render_string('<ul>{% for b in books %}<li>{{ b.title }}</li>{% endfor %}</ul>', {'books': [b.to_dict() for b in Book.all()]})
print('FROND', html)
HTML(html)""")
C.append("print('END')")
nb = nbf.v4.new_notebook(); nb.cells = [nbf.v4.new_code_cell(c) for c in C]
nb.metadata["kernelspec"] = {"name": "python", "display_name": "Python (Pyodide)", "language": "python"}
nbf.write(nb, "content/probe.ipynb")
