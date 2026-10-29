"""Run the 19-scaffolding "Combining Generators" section of every port, docs and book,
against the real framework generators (through the tina4 CLI where the page says `tina4`).

A file is bad if any of these fail:
  * a command in the section's bash block exits non-zero, or does not produce what it names
    (model + migration for `generate model`, a route naming the model for `generate route`);
  * a `tina4 ...` command is not forwarded verbatim to the framework CLI;
  * any `--with...` flag the section names is rejected by `generate model`;
  * a prose claim the section makes is false (migration by default, --no-migration omits it,
    `generate form|view|test` add a piece, "but no form", `generate crud` builds the full set).
"""
import os, re, shlex, shutil, subprocess, sys, tempfile

DOCS, BOOK, RT = sys.argv[1], sys.argv[2], sys.argv[3]  # DOCS or BOOK may be "none" to skip it
SHIMS = os.path.join(RT, "shims")
PORTS = {  # port -> (book dir, project marker files, framework cli)
    "python": ("book-1-python", ["app.py"], "tina4python"),
    "php":    ("book-2-php",    ["index.php", "vendor/"], "tina4php"),
    "ruby":   ("book-3-ruby",   ["app.rb"], "tina4ruby"),
    "nodejs": ("book-4-nodejs", ["app.ts"], "tina4nodejs"),
}
RUNS = tempfile.mkdtemp(prefix="runs-", dir=RT)


def section(path):
    out, on = [], False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## Combining Generators"):
            on = True
        elif on and (line.startswith("## ") or line.startswith("---")):
            break
        if on:
            out.append(line)
    return "".join(out) if out else None


def project(port):
    d = tempfile.mkdtemp(dir=RUNS)
    for m in PORTS[port][1]:
        p = os.path.join(d, m)
        os.makedirs(p) if m.endswith("/") else open(p, "w").close()
    return d


def files(d):
    return {os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs}


def run(d, argv):
    log = os.path.join(d, ".shim.log")
    env = {"HOME": os.path.join(RT, "home"), "PATH": SHIMS + ":/usr/bin:/bin", "SHIM_LOG": log,
           "LANG": "C.UTF-8", "NO_COLOR": "1"}
    before = files(d)
    p = subprocess.run(argv, cwd=d, env=env, capture_output=True, text=True, timeout=120)
    new = files(d) - before - {".shim.log"}
    fwd = open(log).read().splitlines()[-1] if os.path.exists(log) else ""
    out = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, new, fwd, (out[0] if out else "")


def check(path, port):
    probs, notes = [], []
    sec = section(path)
    if sec is None:
        return ["no Combining Generators section"], notes
    fw = PORTS[port][2]
    blocks = re.findall(r"```bash\n(.*?)```", sec, re.S)
    cmds = [shlex.split(l) for b in blocks for l in b.splitlines() if l.strip() and not l.startswith("#")]
    prefix = cmds[0][0] if cmds else ("tina4python" if port == "python" else "tina4")
    d = project(port)
    made, model, migr_by_default = set(), "Product", None
    for argv in cmds:
        rc, new, fwd, first = run(d, argv)
        made |= new
        if argv[0] == "tina4":
            want = " ".join([fw] + argv[1:])
            if fwd == want:
                notes.append(f"forwarded verbatim: {want}")
            else:
                probs.append(f"tina4 did not forward verbatim: got '{fwd}' want '{want}'")
        if rc != 0:
            probs.append(f"`{shlex.join(argv)}` rc={rc}: {first}")
            continue
        if argv[1:3] == ["generate", "model"]:
            model = argv[3]
            m = [f for f in new if f.startswith(("src/orm/", "src/models/")) and model.lower() in f.lower()]
            g = [f for f in new if f.startswith("migrations/") and f"create_{model.lower()}" in f]
            if not m:
                probs.append(f"`{shlex.join(argv)}` wrote no model file")
            if "--no-migration" not in argv:
                migr_by_default = bool(g)
        if argv[1:3] == ["generate", "route"]:
            r = [f for f in new if f.startswith("src/routes/")]
            mi = argv.index("--model") + 1 if "--model" in argv else None
            if not r:
                probs.append(f"`{shlex.join(argv)}` wrote no route file")
            elif mi and not any(argv[mi] in open(os.path.join(d, f)).read() for f in r):
                probs.append(f"`{shlex.join(argv)}` route does not use model {argv[mi]}")
        notes.append(f"ran `{shlex.join(argv)}` rc=0 new={sorted(new)}")

    for flag in sorted(set(re.findall(r"--with[\w-]*", sec))):
        rc, _, _, first = run(project(port), [prefix, "generate", "model", "Probe", "--fields", "name:string", flag])
        if rc != 0:
            probs.append(f"documents {flag}; generate model rejects it: {first}")
        else:
            notes.append(f"{flag} accepted")

    if "migration by default" in sec or "included by default" in sec:
        if migr_by_default is None:
            rc, new, _, _ = run(project(port), [prefix, "generate", "model", "Product", "--fields", "name:string"])
            migr_by_default = rc == 0 and any(f.startswith("migrations/") for f in new)
        if not migr_by_default:
            probs.append("claims generate model writes a migration by default; it did not")
    if "`--no-migration`" in sec:
        rc, new, _, first = run(project(port), [prefix, "generate", "model", "Gadget", "--no-migration"])
        if rc != 0 or any(f.startswith("migrations/") for f in new) or not any("adget" in f for f in new):
            probs.append(f"--no-migration claim false: rc={rc} new={sorted(new)} {first}")
        else:
            notes.append(f"--no-migration: model only, new={sorted(new)}")
    if "but no form" in sec and cmds and any(f.startswith("src/templates/forms/") for f in made):
        probs.append("says 'no form' but the commands wrote a form")
    for g in re.findall(r"`generate (form|view|test)`", sec):
        rc, new, _, first = run(d, [prefix, "generate", g, model])
        if rc != 0 or not new:
            probs.append(f"`generate {g} {model}` rc={rc} new={sorted(new)} {first}")
        else:
            notes.append(f"generate {g} {model}: new={sorted(new)}")
    if "`generate crud`" in sec:
        rc, new, _, first = run(project(port), [prefix, "generate", "crud", model, "--fields", "name:string,price:float"])
        need = {"model": ("src/orm/", "src/models/"), "migration": ("migrations/",), "route": ("src/routes/",),
                "template": ("src/templates/",), "test": ("tests/", "spec/")}
        miss = [k for k, pre in need.items() if not any(f.startswith(pre) for f in new)]
        if rc != 0 or miss:
            probs.append(f"`generate crud` rc={rc} missing={miss} {first}")
        else:
            notes.append(f"generate crud {model}: model+migration+route+templates+test ({len(new)} files)")
    return probs, notes


ok = bad = 0
for port, (bookdir, _, _) in PORTS.items():
    for label, path in ((f"docs/{port}", f"{DOCS}/docs/{port}/19-scaffolding.md"),
                        (f"book/{port}", f"{BOOK}/{bookdir}/chapters/19-scaffolding.md")):
        if path.startswith("none/"):
            continue
        if not os.path.exists(path):
            probs, notes = ["file missing"], []
        else:
            probs, notes = check(path, port)
        print(f"{'BAD ' if probs else 'OK  '}{label}")
        for n in notes:
            print(f"      . {n}")
        for p in probs:
            print(f"      ! {p}")
        ok, bad = ok + (not probs), bad + bool(probs)
shutil.rmtree(RUNS, ignore_errors=True)
print(f"VERDICT: {'FAIL' if bad else 'PASS'} ok={ok} bad={bad} (19-scaffolding Combining Generators, 4 ports, docs={DOCS} book={BOOK})")
sys.exit(1 if bad else 0)
