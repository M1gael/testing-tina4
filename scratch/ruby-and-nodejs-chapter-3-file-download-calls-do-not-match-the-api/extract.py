# extract.py <page.md> <fence-lang> <outdir>
# Writes every fenced <fence-lang> block that calls .file( to <outdir>/b<N>.txt and prints one manifest
# line per block: "<N> <route|stmt> <args:1|2> <route-path or ->". "args" counts top-level arguments of the file( call.
import re, sys, pathlib

page, lang, out = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
text = pathlib.Path(page).read_text()
blocks = re.findall(r"^```" + re.escape(lang) + r"\n(.*?)^```", text, re.S | re.M)


def nargs(src):
    i = src.index(".file(") + len(".file(")
    depth, q, n, seen = 0, None, 1, False
    for c in src[i:]:
        if q:
            if c == q:
                q = None
            continue
        if c in "\"'":
            q, seen = c, True
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return n if seen or n > 1 else 0
            depth -= 1
        elif c == "," and depth == 0:
            n += 1
        elif not c.isspace():
            seen = True
    raise SystemExit("unterminated file( call")


n = 0
for b in blocks:
    if ".file(" not in b:
        continue
    n += 1
    (out / f"b{n}.txt").write_text(b)
    m = re.search(r"Router\.get\(\s*\"([^\"]+)\"", b)
    print(n, "route" if m else "stmt", nargs(b), m.group(1) if m else "-")
