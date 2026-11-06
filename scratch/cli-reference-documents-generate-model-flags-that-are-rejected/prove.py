"""Run the `tina4 generate model|route` commands 31-cli shows, exactly as written, and check them.

usage: python3 -I prove.py <docs-or-book tree> [--rt RT]
For each port's 31-cli.md:
  * every bash line `tina4 generate model|route ...` (and the consecutive ones in the same fence,
    run in order in one fresh project) must exit 0;
  * the ```-fenced output block right after such a fence, when it is all `Created <path>` lines,
    must list exactly the files the commands wrote (timestamps normalised);
  * every flag in the `generate model` Options table must be accepted by `generate model`.
Prints one line per check and `VERDICT: PASS|FAIL ok=N bad=M`; exits 1 on FAIL.
"""
import os, re, subprocess, sys, tempfile, pathlib, shutil

tree = pathlib.Path(sys.argv[1])
RT = pathlib.Path(sys.argv[sys.argv.index("--rt") + 1]) if "--rt" in sys.argv else \
    pathlib.Path.home() / ".cache/tina4-worktrees/docs-cli05/rt"
ENV = dict(os.environ, HOME=str(RT / "home"), PATH=f"{RT}/shims:/usr/bin:/bin")
DOC = {"python": "python", "php": "php", "ruby": "ruby", "nodejs": "nodejs"}
BOOK = {"python": "book-1-python", "php": "book-2-php", "ruby": "book-3-ruby", "nodejs": "book-4-nodejs"}
MARK = {
    "python": {"app.py": "", "requirements.txt": "tina4-python\n"},
    "php": {"composer.json": '{"require":{"tina4stack/tina4php":"*"}}', "index.php": "", "vendor/.keep": ""},
    "ruby": {"Gemfile": 'gem "tina4ruby"\n'},
    "nodejs": {"package.json": '{"dependencies":{"tina4-nodejs":"*"}}', "app.ts": ""},
}
ok = bad = 0

def report(good, msg):
    global ok, bad
    ok += good; bad += not good
    print(("ok   " if good else "BAD  ") + msg)

def project(lang):
    d = pathlib.Path(tempfile.mkdtemp(dir=RT, prefix="prove."))
    for f, c in MARK[lang].items():
        (d / f).parent.mkdir(parents=True, exist_ok=True); (d / f).write_text(c)
    return d

def files(d):
    return {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()
            and not re.match(r"(\.tina4|logs|data|vendor|secrets)(/|$)", str(p.relative_to(d)))}

def run(d, cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=d, env=ENV, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()

norm = lambda s: re.sub(r"\d{14}", "TS", s)

for lang in DOC:
    p = tree / "docs" / DOC[lang] / "31-cli.md"
    if not p.exists():
        p = tree / BOOK[lang] / "chapters/31-cli.md"
    text = p.read_text()
    fences = list(re.finditer(r"```(\w*)\n(.*?)```", text, re.S))
    for i, m in enumerate(fences):
        if m.group(1) != "bash":
            continue
        cmds = [l.strip() for l in m.group(2).splitlines() if re.match(r"\s*tina4 generate (model|route)\b", l)]
        if not cmds:
            continue
        line = text[:m.start()].count("\n") + 1
        d = project(lang); before = files(d); fails = []
        for c in cmds:
            rc, out = run(d, c)
            if rc:
                fails.append(f"{c!r} rc={rc}: {next((o for o in out if o.strip()), '')[:80]}")
        report(not fails, f"{lang}:{line} runs {cmds}" + (f" -- {fails}" if fails else ""))
        nxt = fences[i + 1] if i + 1 < len(fences) else None
        if nxt and nxt.group(1) == "" and text[m.end():nxt.start()].strip() == "":
            lines = [l.strip() for l in nxt.group(2).splitlines() if l.strip()]
            if lines and all(l.startswith("Created ") for l in lines):
                claimed = {norm(l[8:]) for l in lines}
                real = {norm(f) for f in files(d) - before}
                good = claimed == real
                report(good, f"{lang}:{line} output block" + ("" if good else
                       f" -- claimed-not-written {sorted(claimed - real)} written-not-claimed {sorted(real - claimed)}"))
        shutil.rmtree(d)
    # Options table of section 4 (generate model)
    sec = re.search(r"## 4\. tina4 generate model.*?### Options\n(.*?)\n---", text, re.S)
    for flag in re.findall(r"^\| `(--[\w-]+)`", sec.group(1), re.M):
        d = project(lang)
        arg = {"--fields": ' "name:string"', "--table-name": " products"}.get(flag, "")
        rc, out = run(d, f"tina4 generate model Product {flag}{arg}")
        report(rc == 0, f"{lang} options-table {flag} rc={rc}" + ("" if rc == 0 else f": {out[0][:70] if out else ''}"))
        shutil.rmtree(d)

    # The sentence under the table: the general flags pass, anything else is refused.
    if "Apart from these and the general" in sec.group(1):
        for flag, want in (("--dry-run", 0), ("--json", 0), ("--help", 0), ("--with-route", 1), ("--soft-delete", 1)):
            d = project(lang); rc, _ = run(d, f"tina4 generate model Product {flag}"); shutil.rmtree(d)
            report((rc == 0) == (want == 0), f"{lang} note {flag} rc={rc}")

print(f"VERDICT: {'PASS' if bad == 0 else 'FAIL'} ok={ok} bad={bad}")
sys.exit(1 if bad else 0)
