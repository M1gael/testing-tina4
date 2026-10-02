import os
from tina4_python.core import run
run(host="127.0.0.1", port=int(os.environ["PORT"]), no_browser=True, no_reload=True)
