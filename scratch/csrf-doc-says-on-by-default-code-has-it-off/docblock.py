# usage: docblock.py <file.md> <heading text> [nth]  -> prints the nth (1-based) fenced code block after that heading
import sys
p, head = sys.argv[1], sys.argv[2]; nth = int(sys.argv[3]) if len(sys.argv) > 3 else 1
lines = open(p).read().split("\n")
i = next(k for k, l in enumerate(lines) if l.lstrip("#").strip() == head)
blocks, cur, inb = [], [], False
for l in lines[i + 1:]:
    if l.startswith("```"):
        if inb: blocks.append(cur); cur = []
        inb = not inb; continue
    if inb: cur.append(l)
    if len(blocks) >= nth: break
print("\n".join(blocks[nth - 1]))
