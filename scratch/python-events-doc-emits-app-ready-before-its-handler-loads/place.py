# usage: place.py <file.md> <heading> <appdir>
# Writes every ```python block in that section to the project path its lead-in prose names
# (the last `...py` in backticks on the nearest non-blank line above the block). A block with
# no named path is an ERROR. Prints one line per block: "<path>".
import sys, os, re
p, head, app = sys.argv[1:4]
lines = open(p).read().split("\n")
i = next(k for k, l in enumerate(lines) if l.startswith("#") and l.lstrip("#").strip() == head)
level = len(lines[i]) - len(lines[i].lstrip("#"))
prose, cur, inb, keep = "", [], False, False
for l in lines[i + 1:]:
    if not inb and re.match(r"#{1,%d} " % level, l): break
    if l.startswith("```"):
        if inb:
            if keep:
                paths = re.findall(r"`([\w/.-]+\.py)`", prose)
                if not paths: sys.exit("ERROR: block with no named path: " + cur[0])
                dst = os.path.join(app, paths[-1]); os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, "w").write("\n".join(cur) + "\n"); print(paths[-1])
            cur = []; inb = False
        else:
            inb = True; keep = l[3:].strip() == "python"
        continue
    if inb: cur.append(l)
    elif l.strip(): prose = l
