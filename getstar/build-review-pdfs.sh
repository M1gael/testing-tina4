#!/usr/bin/env bash
# build-review-pdfs.sh — reviewable PDFs of every Python page this work changed,
# each one paired with what the live site shows today.
#
#   ./getstar/build-review-pdfs.sh
#
# Output (gitignored) in getstar/review-output/:
#
#   01-overview-BEFORE.pdf          the 621-line quick-reference wall at /python/
#   01-overview-AFTER.pdf           the argument page that replaces it
#   02-getting-started-BEFORE.pdf   the 1132-line chapter
#   02-getting-started-AFTER.pdf    the rewrite
#   03-quick-reference-NEW.pdf      the finder, moved off the landing page
#   04-book-chapter-1-print.pdf     chapter 1 as the downloadable book renders it
#
# BEFORE copies are built from origin/main in a throwaway git worktree, so they
# are the real current pages rather than a description of them.
#
# Each variant is built to static HTML and served by python's http.server for
# printing: no dev server to coordinate, and identical treatment either side.

set -euo pipefail

BOOK=/var/home/work/gitdir/tina4-book
DOCS=/var/home/work/gitdir/tina4-documentation
OUT="$(cd "$(dirname "$0")" && pwd)/review-output"
WORKTREE=/tmp/tina4-docs-before-$$

CHROME=$(command -v chromium || command -v chromium-browser || true)
[[ -z "$CHROME" ]] && { echo "chromium not found; cannot print the site pages" >&2; exit 1; }

mkdir -p "$OUT"
TMP=$(mktemp -d)
cleanup() {
    [[ -n "${SRV_PID:-}" ]] && kill "$SRV_PID" 2>/dev/null || true
    rm -rf "$BOOK/.review-ch1.yml" "$BOOK/.review-out"
    git -C "$DOCS" worktree remove --force "$WORKTREE" 2>/dev/null || true
    rm -rf "$WORKTREE" "$TMP"
}
trap cleanup EXIT

# Each print gets its own port. A reused port let a lingering server from the
# previous call keep serving the previous build, which silently produced a
# "BEFORE" PDF containing the AFTER page — identical bytes, no error.
PORT=8900

# print <dist-dir> <url-path> <output-name> <expected-string>
# The expected string must appear both in what the server returns and in the
# finished PDF; either check failing is fatal, because the failure mode this
# guards against looks exactly like success.
print_page() {
    local dist="$1" path="$2" name="$3" expect="$4"
    PORT=$((PORT + 1))

    [[ -f "$dist/$path" ]] || { echo "✗ $dist/$path was never built" >&2; exit 1; }

    ( cd "$dist" && exec python3 -m http.server "$PORT" >/dev/null 2>&1 ) &
    SRV_PID=$!
    for _ in $(seq 1 30); do
        sleep 0.4
        curl -s -o /dev/null "http://127.0.0.1:$PORT/$path" && break
    done

    # Extract to a file before grepping. Under `set -o pipefail`, `grep -q` exits
    # on first match, pdftotext/curl take SIGPIPE, and the pipeline reports
    # failure even though the match succeeded — which read as a missing string.
    curl -s "http://127.0.0.1:$PORT/$path" > "$TMP/served.html" || true
    if ! grep -qF "$expect" "$TMP/served.html"; then
        echo "✗ served page for $name does not contain '$expect' — wrong build" >&2
        kill "$SRV_PID" 2>/dev/null || true
        exit 1
    fi

    timeout 120 "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
        --print-to-pdf="$OUT/$name" "http://127.0.0.1:$PORT/$path" >/dev/null 2>&1 || true

    kill "$SRV_PID" 2>/dev/null || true; wait "$SRV_PID" 2>/dev/null || true; unset SRV_PID

    pdftotext "$OUT/$name" "$TMP/out.txt" 2>/dev/null || true
    if ! grep -qF "$expect" "$TMP/out.txt"; then
        echo "✗ $name does not contain '$expect'" >&2
        exit 1
    fi
}

# ── AFTER: the branch as it stands ────────────────────────────────────────
echo "▶ building the site from this branch"
( cd "$DOCS" && npm run docs:build >/dev/null 2>&1 )
print_page "$DOCS/docs/.vitepress/dist" "python/index.html" "01-overview-AFTER.pdf" "Why not just use Flask"
print_page "$DOCS/docs/.vitepress/dist" "python/01-getting-started/index.html" "02-getting-started-AFTER.pdf" "Env Configuration"
print_page "$DOCS/docs/.vitepress/dist" "python/quick-reference/index.html" "03-quick-reference-NEW.pdf" "Hot Tips"

# ── BEFORE: the same two pages on origin/main ─────────────────────────────
echo "▶ building the site from origin/main, for comparison"
git -C "$DOCS" worktree add --detach -q "$WORKTREE" origin/main
ln -s "$DOCS/node_modules" "$WORKTREE/node_modules"
( cd "$WORKTREE" && npm run docs:build >/dev/null 2>&1 )
print_page "$WORKTREE/docs/.vitepress/dist" "python/index.html" "01-overview-BEFORE.pdf" "Tina4 Python - Quick Reference"
print_page "$WORKTREE/docs/.vitepress/dist" "python/01-getting-started/index.html" "02-getting-started-BEFORE.pdf" "Prerequisites and Installation"

# ── Chapter 1 as the downloadable book renders it ──────────────────────────
# tina4-book's own generator, so this is the real print artefact rather than a
# web page printed to paper. Needs the pinned deps from scripts/requirements.txt.
VENV="$OUT/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
    echo "▶ installing the book generator's pinned dependencies"
    uv venv -q "$VENV"
    uv pip install -q --python "$VENV/bin/python" -r "$BOOK/scripts/requirements.txt"
fi
cat > "$BOOK/.review-ch1.yml" <<'YML'
title: "Tina4 for Python Developers"
subtitle: "Chapter 1 review copy"
accent: "#306998"
version: "v3.13.97"
cover_logo: "assets/tina4-cover-logo.png"
chapters_dir: "book-1-python/chapters"
output: ".review-out/04-book-chapter-1-print.pdf"
chapters:
  - 01-getting-started.md
YML
echo "▶ chapter 1 through the book generator"
mkdir -p "$BOOK/.review-out"
( cd "$BOOK" && "$VENV/bin/python" scripts/build_pdf.py .review-ch1.yml >/dev/null )
mv "$BOOK/.review-out/04-book-chapter-1-print.pdf" "$OUT/"

echo
echo "Ready to send, in $OUT:"
for f in "$OUT"/*.pdf; do
    [[ -f "$f" ]] || continue
    printf '  %-34s %4s KB  %s pages\n' "$(basename "$f")" \
        "$(( $(stat -c%s "$f") / 1024 ))" "$(pdfinfo "$f" 2>/dev/null | awk '/^Pages/{print $2}')"
done
