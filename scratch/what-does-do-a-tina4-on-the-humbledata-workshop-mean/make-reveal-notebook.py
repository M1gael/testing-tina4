import nbformat as nbf
C = ["!cat solutions/01_01.py", "%load solutions/01_01.py", "%run solutions/01_01.py", "print('PRINT', open('solutions/01_01.py').read())", "print('END')"]
nb = nbf.v4.new_notebook(); nb.cells = [nbf.v4.new_code_cell(c) for c in C]
nb.metadata["kernelspec"] = {"name": "python", "display_name": "Python (Pyodide)", "language": "python"}
nbf.write(nb, "content/probe.ipynb")
