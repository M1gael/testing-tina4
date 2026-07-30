#!/usr/bin/env bash
# Claim D — the "Ask Tina4" widget on tina4.com links further reading to raw
# markdown on GitHub instead of the published docs page, and in one common
# emission shape the link it renders is outright broken.
#
# This talks to the live public endpoint the website itself calls. Read-only:
# it asks a documentation question, exactly as a visitor would. Needs network.
set -u
. "$(dirname "$0")/lib/common.sh"
need curl
need python3

RAG="https://rag.tina4.com/v1/ask"
QUERIES=(
  "How do I define a route?"
  "How do I use the ORM?"
  "How do I run migrations?"
)

head1 "Claim D — Ask Tina4 further-reading links"
dim "The widget config on tina4.com is:"
dim '  __TP_CHAT__={"api":"https://rag.tina4.com","label":"Ask Tina4",...}'
dim "and /assets/client.js POSTs {query, language, k:6, stream:false} to /v1/ask."

OUT="$RUN_DIR/ask"
mkdir -p "$OUT"

for q in "${QUERIES[@]}"; do
  head2 "Q: $q"
  slug="$(printf '%s' "$q" | tr -cd '[:alnum:] ' | tr ' ' '_')"
  body="$(python3 -c 'import json,sys; print(json.dumps({"query":sys.argv[1],"language":"python","k":6,"stream":False}))' "$q")"
  code="$(curl -s -X POST "$RAG" -H 'Content-Type: application/json' -d "$body" \
          -o "$OUT/$slug.json" -w '%{http_code}')"
  if [ "$code" != "200" ]; then
    warn "endpoint returned HTTP $code — skipping (network or service issue)"
    continue
  fi
  python3 - "$OUT/$slug.json" <<'PY'
import json, re, sys

d = json.load(open(sys.argv[1]))
answer = d.get("answer") or d.get("response") or d.get("text") or ""

links = re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', answer)
if not links:
    print("    (no markdown links in this answer)")
else:
    print("    links in the answer text:")
    for text, url in links:
        print(f"      [{text}] -> {url}")

srcs = d.get("sources") or []
if srcs:
    print("    sources[] urls:")
    for s in srcs[:3]:
        print(f"      {s.get('url')}")

# Replay the site's own md() transform: escape, then apply its link regex.
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
html = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
              r'<a href="\2" target="_blank" rel="noreferrer">\1</a>',
              esc(answer))
anchors = re.findall(r'<a href="[^"]*"[^>]*>[^<]*</a>', html)
if anchors:
    print("    what the browser actually receives:")
    for a in anchors:
        broken = "&lt;" in a.split('href="')[1].split('"')[0]
        flag = "   <-- BROKEN: relative href, will 404" if broken else ""
        print(f"      {a}{flag}")

# Map GitHub book paths to the published page. Use the inline links when the
# answer has them, otherwise fall back to sources[] — the GitHub url is in the
# index either way, so the finding holds regardless of how the model phrased it.
candidates = [u for _, u in links] or [s.get("url", "") for s in srcs]
seen, rows = set(), []
for url in candidates:
    m = re.search(r'book-\d+-([a-z]+)/chapters/([0-9a-z-]+)\.md', url)
    if not m:
        continue
    lang, chap = m.groups()
    if (lang, chap) in seen:
        continue
    seen.add((lang, chap))
    rows.append((url.strip("<>"), f"https://tina4.com/{lang}/{chap}/"))
if rows:
    src = "answer link" if links else "sources[] (answer had no inline link)"
    print(f"    where the link goes vs where the page lives — from {src}:")
    for indexed, correct in rows:
        print(f"      indexed : {indexed}")
        print(f"      correct : {correct}")
PY
done

head2 "D2 — the angle-bracket form, replayed"
dim "The model does not always emit the same link syntax, so the broken variant may"
dim "not appear in the live answers above. This replays a real captured response"
dim "through the site's own md() helper so you can see what it does either way."
python3 - <<'PY'
import re

# Captured verbatim from rag.tina4.com for "How do I define a route?" —
# CommonMark's angle-bracket destination form, which is valid markdown.
answer = ("These routes will register as `/api/v1/users`. "
          "[source](<https://github.com/tina4stack/tina4-book/blob/main/"
          "book-1-python/chapters/02-routing.md>)")

# tina4.com /assets/client.js, md(): escape first, then apply the link regex.
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
html = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
              r'<a href="\2" target="_blank" rel="noreferrer">\1</a>',
              esc(answer))
anchor = re.search(r'<a href="[^"]*"[^>]*>[^<]*</a>', html).group(0)
href = anchor.split('href="')[1].split('"')[0]

print(f"    markdown in  : [source](<https://github.com/...02-routing.md>)")
print(f"    href out     : {href[:70]}...")
print(f"    absolute?    : {href.startswith(('http://', 'https://'))}")
if not href.startswith(("http://", "https://")):
    print("    -> the escaped angle bracket makes this a RELATIVE url; it 404s.")
PY

head2 "Verifying the correct destinations actually exist"
for u in https://tina4.com/python/02-routing/ https://tina4.com/python/06-orm/; do
  printf '  %-42s HTTP %s\n' "$u" "$(curl -s -o /dev/null -w '%{http_code}' "$u")"
done
printf '  %-42s HTTP %s\n' "the mangled angle-bracket href" \
  "$(curl -s -o /dev/null -w '%{http_code}' 'https://tina4.com/python/%3Chttps://github.com/tina4stack/tina4-book/blob/main/book-1-python/chapters/02-routing.md%3E')"

head2 "What to make of it"
cat <<'TXT'
  Two separate defects.

  D1 — the RAG index stores a GitHub blob URL as each chunk's `url`, so both the
       answer's [source](...) link and every sources[] entry point at raw
       markdown. The published page exists and the mapping is mechanical:
         .../book-1-python/chapters/06-orm.md  ->  https://tina4.com/python/06-orm/
       The website frontend does no rewriting at all, so this has to be fixed at
       ingest: store the site URL, and keep the GitHub one in a separate field if
       an "edit this page" link is wanted.

  D2 — when the model emits the CommonMark angle-bracket form, [source](<url>),
       the site's own md() helper escapes first and then captures the brackets
       into the href. The result is href="&lt;https://...&gt;", which is a
       RELATIVE url and 404s. Strip a wrapping <> from the destination and
       reject anything that is not http(s): or site-relative.
TXT
