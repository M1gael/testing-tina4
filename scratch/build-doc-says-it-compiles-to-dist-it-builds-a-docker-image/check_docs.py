#!/usr/bin/env python3
"""d-cli-03 doc check. Usage: check_docs.py DOCS_ROOT BOOK_ROOT (either may be "-").

Wrong: any page that says `tina4 build` compiles TypeScript / bundles / writes dist/,
or a plain-server `set -e` script that runs `tina4 build`.
Missing: a page the fix targets that does not say `tina4 build` builds a Docker image.
"""
import re
import sys
from pathlib import Path

# Applied to every .md in scope (the remaining-instance sweep).
WRONG_LINE = [
    ("W1 fake TS build output", re.compile(r"Compiled \d+ TypeScript files")),
    ("W2 fake dist/ output", re.compile(r"Output: dist/")),
    ("W3 'compiles TypeScript'", re.compile(r"Compiles TypeScript to JavaScript")),
    ("W4 fake 'Building for production'", re.compile(r"Building for production\.\.\.")),
    ("W5 build comment says bundle/minify/TS/dist",
     re.compile(r"tina4 build\b.*#.*(?i:bundle|minify|typescript|dist/|all build steps)")),
    ("W6 cli table says front-end assets",
     re.compile(r"\|\s*`tina4 build`\s*\|\s*Build production front-end assets")),
]

# Pages the fix targets: (relative path, regex that the corrected text must match).
DOCS_TARGETS = {
    "docs/general/cli.md": r"\|\s*`tina4 build`\s*\|[^|\n]*Docker",
    "docs/nodejs/31-cli.md": r"## 14\. tina4 build[^\n]*\n(?:(?!\n## )[\s\S])*Dockerfile",
    "docs/nodejs/34-deployment.md": r"## 3\. Building for Production(?:(?!\n## )[\s\S])*Dockerfile",
    "docs/ruby/31-cli.md": r"tina4 build\s+#[^\n]*Docker",
    "docs/ruby/index.md": r"tina4 build\s+#[^\n]*Docker",
}
BOOK_TARGETS = {
    "book-3-ruby/chapters/31-cli.md": DOCS_TARGETS["docs/ruby/31-cli.md"],
    "book-4-nodejs/chapters/31-cli.md": DOCS_TARGETS["docs/nodejs/31-cli.md"],
    "book-4-nodejs/chapters/34-deployment.md": DOCS_TARGETS["docs/nodejs/34-deployment.md"],
}

FENCE = re.compile(r"```(?:bash|sh)\n([\s\S]*?)```")


def section(text, heading_re):
    m = re.search(heading_re, text)
    if not m:
        return ""
    rest = text[m.end():]
    end = re.search(r"\n## ", rest)
    return rest[: end.start()] if end else rest


def scan(root, scope_globs, targets, hits, missing):
    root = Path(root)
    files = sorted({p for g in scope_globs for p in root.glob(g)})
    if not files:
        missing.append(f"{root}: no files in scope")
    for p in files:
        rel = p.relative_to(root).as_posix()
        text = p.read_text(errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            for name, rx in WRONG_LINE:
                if rx.search(line):
                    hits.append(f"{root.name}/{rel}:{n}: {name}: {line.strip()[:90]}")
        if rel.endswith("34-deployment.md") and "nodejs" in rel:
            # W7: §3 tells you to run node dist/app.js after `tina4 build`.
            if "node dist/app.js" in section(text, r"## 3\. Building for Production"):
                hits.append(f"{root.name}/{rel}: W7 §3 runs node dist/app.js after tina4 build")
        for block in FENCE.findall(text):
            # W8: a plain-server set -e script that runs tina4 build (exits 1, aborts deploy).
            if "set -e" in block and re.search(r"^tina4 build\b", block, re.M) \
                    and "docker" not in block:
                hits.append(f"{root.name}/{rel}: W8 set -e server script runs tina4 build")
    for rel, rx in targets.items():
        p = root / rel
        if not p.is_file():
            missing.append(f"{root.name}/{rel}: target page not found")
        elif not re.search(rx, p.read_text(errors="replace")):
            missing.append(f"{root.name}/{rel}: does not say tina4 build builds a Docker image")


def main():
    docs, book = sys.argv[1], sys.argv[2]
    hits, missing = [], []
    if docs != "-":
        scan(docs, ["docs/general/**/*.md", "docs/nodejs/**/*.md", "docs/ruby/**/*.md",
                    "docs/python/**/*.md", "docs/php/**/*.md"], DOCS_TARGETS, hits, missing)
    if book != "-":
        scan(book, ["book-*/chapters/**/*.md"], BOOK_TARGETS, hits, missing)
    for h in hits:
        print("WRONG   " + h)
    for m in missing:
        print("MISSING " + m)
    ok = not hits and not missing
    print(f"VERDICT: {'PASS' if ok else 'FAIL'} wrong={len(hits)} missing={len(missing)}"
          f" docs={docs} book={book}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
