#!/usr/bin/env bash
# build-review-pdfs.sh — produce reviewable PDFs of the three Python pages.
#
# For sending a reviewer something readable without asking them to clone two
# repos and run a Node toolchain. Output lands in getstar/review-output/,
# which is gitignored.
#
#   ./getstar/build-review-pdfs.sh
#
# Two different generators, deliberately:
#
#   Chapter 1  -> tina4-book/scripts/build_pdf.py, the project's own book
#                 generator. What the reader gets in the downloadable PDF,
#                 so reviewing it in this form reviews the real artefact.
#
#   Landing +  -> headless Chromium against a running docs dev server. These
#   quick ref     two pages are site-only (non-numbered, never in the book),
#                 so printing the rendered page is the only faithful option.

set -euo pipefail

BOOK=/var/home/work/gitdir/tina4-book
DOCS=/var/home/work/gitdir/tina4-documentation
OUT="$(cd "$(dirname "$0")" && pwd)/review-output"
PORT=5180

mkdir -p "$OUT"

# ── Chapter 1, via the book's own PDF generator ───────────────────────────
# Needs the pinned deps from tina4-book/scripts/requirements.txt. Kept in a
# throwaway venv so nothing is installed system-wide.
VENV="$OUT/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
    echo "▶ installing the book generator's pinned dependencies"
    uv venv -q "$VENV"
    uv pip install -q --python "$VENV/bin/python" -r "$BOOK/scripts/requirements.txt"
fi

# build_pdf.py resolves paths against its repo root, so the config has to live
# inside the book repo. Written and removed here rather than committed.
cat > "$BOOK/.review-ch1.yml" <<'YML'
title: "Tina4 for Python Developers"
subtitle: "Chapter 1 review copy"
accent: "#306998"
version: "v3.13.97"
cover_logo: "assets/tina4-cover-logo.png"
chapters_dir: "book-1-python/chapters"
output: ".review-out/REVIEW-ch1-getting-started.pdf"
chapters:
  - 01-getting-started.md
YML
trap 'rm -rf "$BOOK/.review-ch1.yml" "$BOOK/.review-out"' EXIT

echo "▶ chapter 1, via the book generator"
mkdir -p "$BOOK/.review-out"
( cd "$BOOK" && "$VENV/bin/python" scripts/build_pdf.py .review-ch1.yml )
mv "$BOOK/.review-out/REVIEW-ch1-getting-started.pdf" "$OUT/"

# ── The two site-only pages, via headless Chromium ────────────────────────
CHROME=$(command -v chromium || command -v chromium-browser || true)
if [[ -z "$CHROME" ]]; then
    echo "⚠ no chromium found — skipping the landing page and quick reference." >&2
    echo "  Chapter 1 is in $OUT" >&2
    exit 0
fi

# Reuse a dev server if one is already up; otherwise start one and stop it after.
STARTED_SERVER=0
if ! curl -s -o /dev/null --max-time 3 "http://localhost:$PORT/python/"; then
    echo "▶ starting a docs dev server on :$PORT"
    ( cd "$DOCS" && npm run docs:dev > "$OUT/dev-server.log" 2>&1 & )
    STARTED_SERVER=1
    for _ in $(seq 1 40); do
        sleep 1
        curl -s -o /dev/null "http://localhost:$PORT/python/" && break
    done
fi

for pair in "python/:REVIEW-overview" "python/quick-reference/:REVIEW-quick-reference"; do
    url="${pair%%:*}"; name="${pair##*:}"
    echo "▶ $name, via headless chromium"
    timeout 120 "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
        --print-to-pdf="$OUT/$name.pdf" "http://localhost:$PORT/$url" >/dev/null 2>&1 || true
done

if [[ "$STARTED_SERVER" == "1" ]]; then
    pid=$(ss -lptn "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
fi

echo
echo "Done. In $OUT:"
for f in "$OUT"/*.pdf; do
    [[ -f "$f" ]] || continue
    pages=$(pdfinfo "$f" 2>/dev/null | awk '/^Pages/{print $2}')
    printf '  %-34s %4s KB  %s pages\n' "$(basename "$f")" "$(( $(stat -c%s "$f") / 1024 ))" "${pages:-?}"
done
