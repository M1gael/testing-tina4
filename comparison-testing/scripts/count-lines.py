#!/usr/bin/env python3
"""count-lines.py — the counter for comparison-testing, with the rules encoded.

Usage:
    scripts/count-lines.py apps/python/tina4 apps/python/flask ...
    scripts/count-lines.py --markdown apps/python/*        # table for a results file

Counting is scripted so a re-run reproduces the number exactly; readme.md rule 8.

What counts
===========
Each app declares its own inventory in a ``manifest.toml`` at its root, because only the
person who built it knows which files they authored and which lines they had to change
inside generated boilerplate. The script does the arithmetic; the manifest records the
judgement calls, in the open, where they can be argued with.

    [app]
    framework = "flask"
    version   = "3.1.3"
    language   = "Python 3.14.5"
    openapi_path = "/openapi.json"

    # Files the developer wrote from nothing.
    authored = ["app.py", "templates/base.html", "templates/bookmarks.html"]

    # Lines changed inside files a scaffolder generated. Counted separately
    # because "I edited 5 of Django's 130 settings lines" is not the same
    # claim as "I wrote 5 lines".
    [edited]
    "config/settings.py" = 2
    "config/urls.py"     = 4

    # Lines whose only job is framework setup, not application logic.
    # A subset of the authored count, reported alongside it.
    wiring_lines = 2

    # Third-party distributions beyond the framework itself. Named, because
    # the list IS the argument; readme.md rule 5.
    packages_added = ["pyjwt", "flask-sqlalchemy", "apispec"]

    # Install measured on a clean venv, before the app was ever run; rule 6.
    # Running the app fills site-packages with __pycache__, so this cannot be
    # re-read afterwards — it is recorded here instead.
    [install]
    measured_before_first_run = true
    distributions = 17
    size_mb = 17.9

A blank or comment-only line never counts, in any language. Nothing is inferred from the
directory contents: a file absent from the manifest is not counted, so an app cannot be
made to look smaller by forgetting to list something without that omission being visible
in the manifest itself.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# Comment prefixes per suffix. HTML/Twig block comments are handled separately.
LINE_COMMENTS = {
    ".py": ("#",),
    ".rb": ("#",),
    ".sh": ("#",),
    ".php": ("//", "#"),
    ".js": ("//",),
    ".ts": ("//",),
    ".toml": ("#",),
    ".env": ("#",),
}
BLOCK_COMMENTS = {
    ".html": ("<!--", "-->"),
    ".twig": ("{#", "#}"),
    ".css": ("/*", "*/"),
    ".scss": ("//", None),
}


def count_file(path: Path) -> int:
    """Non-blank, non-comment lines in one file."""
    suffix = path.suffix.lower()
    line_markers = LINE_COMMENTS.get(suffix, ())
    block_open, block_close = BLOCK_COMMENTS.get(suffix, (None, None))

    total = 0
    in_block = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_block:
            if block_close and block_close in line:
                in_block = False
            continue
        if block_open and line.startswith(block_open):
            # A one-line block comment opens and closes on the same line.
            if not (block_close and block_close in line):
                in_block = True
            continue
        if line_markers and line.startswith(line_markers):
            continue
        total += 1
    return total


class App:
    def __init__(self, root: Path):
        self.root = root
        manifest_path = root / "manifest.toml"
        if not manifest_path.exists():
            raise SystemExit(
                f"{root}: no manifest.toml. Every app declares its own inventory — "
                "see the docstring in scripts/count-lines.py."
            )
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        meta = data.get("app", {})

        self.framework: str = meta.get("framework", root.name)
        self.version: str = meta.get("version", "?")
        self.language: str = meta.get("language", "?")
        self.openapi_path: str = meta.get("openapi_path", "?")
        self.wiring: int = int(meta.get("wiring_lines", 0))
        self.packages: list[str] = list(meta.get("packages_added", []))
        self.authored_files: list[str] = list(meta.get("authored", []))
        self.edited: dict[str, int] = {k: int(v) for k, v in data.get("edited", {}).items()}
        self.install: dict = data.get("install", {})
        self.notes: str = meta.get("notes", "")

        self.missing = [f for f in self.authored_files if not (root / f).exists()]
        self.per_file = {
            f: count_file(root / f) for f in self.authored_files if (root / f).exists()
        }

    @property
    def authored_lines(self) -> int:
        return sum(self.per_file.values())

    @property
    def edited_lines(self) -> int:
        return sum(self.edited.values())

    @property
    def total_lines(self) -> int:
        return self.authored_lines + self.edited_lines

    @property
    def files_touched(self) -> int:
        return len(self.per_file) + len(self.edited)

    def site_packages(self) -> tuple[int, str]:
        """(distribution count, human size) for the app's venv, or (-1, '?').

        Install size must be read before the app is ever run (readme rule 6), and
        running it is also mandatory (rule 2) — the two cannot both hold for a live
        venv. So the manifest carries the pre-run measurement as data:

            [install]
            measured_before_first_run = true
            distributions = 17
            size_mb = 17.9

        Those values win when present. Without them the venv is measured live, and a
        venv containing __pycache__ is reported as stale, because that is exactly how
        an earlier Tina4 figure came out 1.5 MB too big.
        """
        if self.install:
            return int(self.install.get("distributions", -1)), f"{float(self.install.get('size_mb', 0)):.1f} MB"

        candidates = sorted(self.root.glob(".venv/lib/python*/site-packages"))
        if not candidates:
            return -1, "?"
        sp = candidates[0]
        dists = len(list(sp.glob("*.dist-info")))
        size = sum(f.stat().st_size for f in sp.rglob("*") if f.is_file())
        pycache = any(sp.rglob("__pycache__"))
        human = f"{size / 1_048_576:.1f} MB" + (" (stale: __pycache__ present)" if pycache else "")
        return dists, human


def report_text(apps: list[App]) -> None:
    for app in apps:
        print(f"\n=== {app.framework} {app.version} — {app.root} ===")
        if app.missing:
            print("  MISSING files listed in manifest.authored:")
            for f in app.missing:
                print(f"    {f}")
        for name, n in app.per_file.items():
            print(f"  {n:>5}  {name}")
        for name, n in app.edited.items():
            print(f"  {n:>5}  {name}  (edited in generated file)")
        dists, size = app.site_packages()
        print(f"  {'-' * 40}")
        print(f"  authored lines   {app.authored_lines}")
        print(f"  edited lines     {app.edited_lines}")
        print(f"  TOTAL            {app.total_lines}")
        print(f"  files touched    {app.files_touched}")
        print(f"  wiring lines     {app.wiring}")
        print(f"  packages added   {len(app.packages)}  {', '.join(app.packages) or '(none)'}")
        print(f"  distributions    {dists if dists >= 0 else 'no .venv found'}")
        print(f"  install size     {size}")
        if app.notes:
            print(f"  notes            {app.notes}")


def report_markdown(apps: list[App]) -> None:
    head = ["Metric"] + [a.framework for a in apps]
    rows = [
        ["Lines you write"] + [str(a.authored_lines) for a in apps],
        ["Lines you must edit"] + [str(a.edited_lines) for a in apps],
        ["**Total lines**"] + [f"**{a.total_lines}**" for a in apps],
        ["Files touched"] + [str(a.files_touched) for a in apps],
        ["Framework-wiring lines"] + [str(a.wiring) for a in apps],
        ["Packages added"] + [str(len(a.packages)) for a in apps],
        ["Distributions installed"] + [
            (str(d) if (d := a.site_packages()[0]) >= 0 else "?") for a in apps
        ],
        ["Install size"] + [a.site_packages()[1] for a in apps],
        ["Version"] + [a.version for a in apps],
    ]
    print("| " + " | ".join(head) + " |")
    print("|" + "|".join(["---"] + ["--:"] * len(apps)) + "|")
    for row in rows:
        print("| " + " | ".join(row) + " |")
    print("\nPackages each framework had to add:\n")
    for a in apps:
        listed = ", ".join(f"`{p}`" for p in a.packages) or "**none**"
        print(f"- **{a.framework}** — {listed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("apps", nargs="+", type=Path, help="app directories, each with a manifest.toml")
    parser.add_argument("--markdown", action="store_true", help="emit a table for a results file")
    args = parser.parse_args()

    apps = [App(p) for p in args.apps if p.is_dir()]
    if not apps:
        print("no app directories given", file=sys.stderr)
        return 2

    if args.markdown:
        report_markdown(apps)
    else:
        report_text(apps)

    stale = [a.framework for a in apps if "stale" in a.site_packages()[1]]
    if stale:
        print(
            f"\nWARNING: {', '.join(stale)} has __pycache__ in site-packages, so the install "
            "size is inflated. Re-create the venv and measure before the app is ever run "
            "(readme.md rule 6).",
            file=sys.stderr,
        )
    missing = [a.framework for a in apps if a.missing]
    if missing:
        print(f"\nERROR: manifest lists files that do not exist for: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
