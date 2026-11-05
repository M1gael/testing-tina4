#!/usr/bin/env python3
"""d-orm-04: does each ch05 'Generating a Migration' section list every file the port's own
`generate migration` writes? Runs the real generators (tip trees in $R), then reads the pages.
Usage: DOCS=<docs tree> or BOOK=<book tree> python3 prove.py   -> PASS rc0 / FAIL rc1 / ERROR rc2"""
import os, re, shutil, subprocess, sys, tempfile, pathlib
R = pathlib.Path(os.environ.get("R", pathlib.Path.home() / ".cache/tina4-worktrees/grind-1102/dorm04"))
PY = 'import sys; from tina4_python.cli import main; sys.argv[0]="tina4python"; main()'
CLI = {
 "python": ["env", f"PYTHONPATH={R}/fw-python", "python3", "-c", PY],
 "php":    ["php", f"{R}/fw-php/bin/tina4php"],
 "ruby":   ["ruby", "-I", f"{R}/fw-ruby/lib", f"{R}/fw-ruby/exe/tina4ruby"],
 "nodejs": [f"{R}/fw-nodejs/node_modules/.bin/tsx", f"{R}/fw-nodejs/packages/cli/src/bin.ts"],
}
BOOK = {"python": "book-1-python", "php": "book-2-php", "ruby": "book-3-ruby", "nodejs": "book-4-nodejs"}
NUM = {"two": 2, "three": 3, "four": 4}
def err(m): print("ERROR:", m); sys.exit(2)

def generate(lang, name):
    d = tempfile.mkdtemp(); h = tempfile.mkdtemp()
    try:
        r = subprocess.run(CLI[lang] + ["generate", "migration", name], cwd=d, capture_output=True,
                           text=True, env={**os.environ, "HOME": h}, timeout=120)
        files = sorted(str(p.relative_to(d)) for p in pathlib.Path(d).rglob("*") if p.is_file())
        if r.returncode != 0 or not files: err(f"{lang} generator rc={r.returncode} files={files}\n{r.stderr[-800:]}")
        return files
    except FileNotFoundError as e: err(f"{lang}: {e}")
    finally: shutil.rmtree(d); shutil.rmtree(h)

docs, book = os.environ.get("DOCS"), os.environ.get("BOOK")
if bool(docs) == bool(book): err("set exactly one of DOCS= or BOOK=")
root = pathlib.Path(docs or book)
bad = ok = 0
for lang in CLI:
    page = root / ("docs/%s/05-database.md" % lang if docs else BOOK[lang] + "/chapters/05-database.md")
    if not page.is_file(): err(f"missing {page}")
    m = re.search(r"^### Generating a Migration\n(.*?)(?=^### )", page.read_text(), re.S | re.M)
    if not m: err(f"no 'Generating a Migration' section in {page}")
    sec = m.group(1)
    name = re.search(r"generate migration (create_\w+)", sec).group(1)
    files = generate(lang, name)
    # the generator's names, with the timestamp prefix and the per-port test casing kept as written
    missing = [f for f in files if not re.search(re.escape(re.sub(r"\d{14}", "@", f)).replace("@", r"\d+"), sec)]
    counts = [NUM[w] for w in re.findall(r"\b(two|three|four) files\b", sec)]
    wrong_count = [c for c in counts if c != len(files)]
    stale = re.findall(r"both the up and down files", sec)
    short = generate(lang, "add_category_to_product")      # the section's claim about non-create names
    claim_short = "writes just the two SQL files" in sec
    short_wrong = claim_short and len(short) != 2
    rel = page.relative_to(root)
    if missing or wrong_count or stale or short_wrong:
        bad += 1
        print(f"FAIL {rel}: generator wrote {files}; missing from page {missing}; "
              f"count words {counts}{'; says both the up and down files' if stale else ''}"
              f"{'; non-create claim wrong: ' + str(short) if short_wrong else ''}")
    else:
        ok += 1; print(f"ok   {rel}: lists all {len(files)} files {files}")
print(f"{'PASS' if bad == 0 else 'FAIL'} ok={ok} bad={bad}")
sys.exit(0 if bad == 0 else 1)
