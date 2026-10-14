import nbformat as nbf
C = ["""import sqlite3
for path in ['data/w1.db', '/tmp/w1.db']:
    for mode in ['DELETE', 'WAL']:
        p = path.replace('w1', 'w1' + mode)
        try:
            c = sqlite3.connect(p); r = c.execute(f'PRAGMA journal_mode={mode}').fetchone(); c.execute('create table if not exists t(x)'); c.execute('insert into t values (1)'); c.commit(); print('JM', p, mode, 'ok', r)
        except Exception as e:
            print('JM', p, mode, type(e).__name__, e)""", "print('END')"]
nb = nbf.v4.new_notebook(); nb.cells = [nbf.v4.new_code_cell(c) for c in C]
nb.metadata["kernelspec"] = {"name": "python", "display_name": "Python (Pyodide)", "language": "python"}
nbf.write(nb, "content/probe.ipynb")
