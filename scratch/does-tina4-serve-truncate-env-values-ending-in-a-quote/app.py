import os, sys
# Stand-in for the framework. tina4 serve spawns `python3 app.py --managed`
# and the child inherits whatever the CLI put in its own environment.
keys = ["TINA4_CSP", "PLAIN_TRAILING_SQ", "SQ_WRAPPED", "DQ_WRAPPED",
        "ENDS_DQ", "TRIPLE_SQ", "QUOTED_EMPTY", "PORT"]
out = os.environ.get("DUMP_TO", "dump.txt")
with open(out, "w") as f:
    for k in keys:
        v = os.environ.get(k)
        f.write("%s=%s\n" % (k, "<unset>" if v is None else v))
sys.exit(0)
