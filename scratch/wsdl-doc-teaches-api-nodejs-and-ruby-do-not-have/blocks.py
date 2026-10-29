# usage: blocks.py <file.md> <heading text> <lang> <outdir>
# Writes every ```<lang> block in that heading's section (up to the next heading of the same or higher
# level) to <outdir>, verbatim, and prints one line per block: "<file>\t<path named on its first line or ->".
import sys, os, re
p, head, lang, out = sys.argv[1:5]
lines = open(p).read().split("\n")
i = next(k for k, l in enumerate(lines) if l.startswith("#") and l.lstrip("#").strip() == head)
level = len(lines[i]) - len(lines[i].lstrip("#"))
blocks, cur, inb, keep = [], [], False, False
for l in lines[i + 1:]:
    if not inb and re.match(r"#{1,%d} " % level, l): break
    if l.startswith("```"):
        if inb:
            if keep: blocks.append(cur)
            cur = []; inb = False
        else:
            inb = True; keep = l[3:].strip() == lang
        continue
    if inb: cur.append(l)
os.makedirs(out, exist_ok=True)
for n, b in enumerate(blocks, 1):
    f = os.path.join(out, "%02d.%s" % (n, lang)); open(f, "w").write("\n".join(b) + "\n")
    m = re.match(r"\s*(?://|#)\s*(src/\S+\.(?:ts|rb))\s*$", b[0]) if b else None
    print("%s\t%s" % (f, m.group(1) if m else "-"))
