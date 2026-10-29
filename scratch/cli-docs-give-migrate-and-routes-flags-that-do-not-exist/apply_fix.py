# usage: apply_fix.py <docs|book> <repo root> [piece ...]   pieces: migrate routes reset phptable  (default all)
# Edits the CLI invocations that no framework CLI accepts. Kept here as the reproducible source of fix.patch.
import re, sys, pathlib
kind, root = sys.argv[1], pathlib.Path(sys.argv[2]); pieces = set(sys.argv[3:]) or {"migrate", "routes", "reset", "phptable"}
L = {"python": "book-1-python", "php": "book-2-php", "ruby": "book-3-ruby", "nodejs": "book-4-nodejs"}
def p(lang, f):
    if kind == "docs": return root / ("docs/general" if lang == "general" else f"docs/{lang}") / f
    return root / ("book-0-understanding" if lang == "general" else L[lang]) / "chapters" / f
def edit(path, fn):
    if not path.exists(): return
    s = path.read_text(); n = fn(s)
    if n == s: sys.exit(f"no change: {path}")
    path.write_text(n)
FILTER_BLOCK = re.compile(r"### Filtering\n\n```bash\n(?:#.*\n|tina4 routes --.*\n|\n)*?```\n\n")
def routing(s):  # 02-routing: drop the --method / --filter examples and their sample output
    s2 = re.sub(r"Filter by method:\n\n```bash\ntina4 routes --method POST\n```\n\n```\n.*?```\n\nSearch for a path pattern:\n\n```bash\ntina4 routes --filter users\n```\n\n```\n.*?```\n\n", "", s, flags=re.S)
    return s2.replace("Filter by method or search for a path pattern:\n\n```bash\ntina4 routes --method POST\ntina4 routes --filter users\n```\n\n", "")
langs = ["python", "php", "ruby", "nodejs"]
if "migrate" in pieces:
    for l in langs:
        edit(p(l, "31-cli.md"), lambda s: s.replace("tina4 migrate --rollback\n", "tina4 migrate:rollback\n").replace("tina4 migrate --status\n", "tina4 migrate:status\n"))
    edit(p("general", "02-architecture.md"), lambda s: s.replace("runs on `tina4 migrate --rollback`", "runs on `tina4 migrate:rollback`"))
    if kind == "docs":
        edit(p("nodejs", "index.md"), lambda s: s.replace("`tina4 migrate --rollback`", "`tina4 migrate:rollback`").replace("`tina4 migrate --status`", "`tina4 migrate:status`").replace("tina4 migrate --rollback\n", "tina4 migrate:rollback\n").replace("tina4 migrate --status\n", "tina4 migrate:status\n"))
        edit(p("php", "index.md"), lambda s: s.replace("tina4 migrate --rollback\n", "tina4 migrate:rollback\n"))
if "routes" in pieces:
    for l in langs:
        edit(p(l, "31-cli.md"), lambda s: FILTER_BLOCK.sub("", s, count=1))
        edit(p(l, "02-routing.md"), routing)
    edit(p("php", "31-cli.md"), lambda s: s.replace("tina4 routes --filter tasks\n", "tina4 routes\n"))
if "reset" in pieces:  # ruby: migrate:reset / migrate:fresh are not commands
    edit(p("ruby", "31-cli.md"), lambda s: s.replace("### Other Migration Commands\n\n```bash\ntina4 migrate:reset        # Roll back all migrations\ntina4 migrate:fresh        # Roll back and re-run all migrations\n```\n\n", ""))
if "phptable" in pieces:  # php: flag table lists three flags tina4php migrate does not take
    edit(p("php", "31-cli.md"), lambda s: s.replace(
        "### Options\n\n| Flag | Description | Example |\n|------|-------------|---------|\n| `--rollback` | Undo the last migration | `tina4 migrate --rollback` |\n| `--rollback-all` | Undo all migrations | `tina4 migrate --rollback` |\n| `--status` | Show migration status | `tina4 migrate --status` |\n",
        "### Related Commands\n\n| Command | Description |\n|---------|-------------|\n| `tina4 migrate:rollback` | Undo the last batch of migrations |\n| `tina4 migrate:status` | Show migration status |\n"))
