import os, sys
# Stand-in for the framework: `tina4 serve` spawns `python3 app.py --managed`,
# and the child inherits whatever the CLI put in its own environment.
keys = ["FIRST_KEY", "SECOND_KEY", "PORT"]
with open(os.environ.get("DUMP_TO", "dump.txt"), "w") as f:
    for k in keys:
        v = os.environ.get(k)
        f.write("%s=%s\n" % (k, "<unset>" if v is None else v))
    # Any key the child received with bytes glued on it.
    for k in sorted(os.environ):
        if k.endswith("FIRST_KEY") and k != "FIRST_KEY":
            f.write("GLUED=%r\n" % k)
sys.exit(0)
