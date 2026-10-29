# usage: doccmds.py <file.md>  -> every `tina4 migrate*` / `tina4 routes` command the page tells the reader to run,
# verbatim: lines of fenced code blocks, and inline `code` spans. Trailing "# comment" stripped.
import re, sys
s = open(sys.argv[1]).read(); out = []; inb = False
for line in s.split("\n"):
    if line.startswith("```"): inb = not inb; continue
    cands = [line.strip()] if inb else re.findall(r"`(tina4 [^`]+)`", line)
    for c in cands:
        c = re.sub(r"\s+#.*$", "", c).strip()
        if re.match(r"tina4 (migrate(:\S+)?|routes)(\s|$)", c): out.append(c)
for c in dict.fromkeys(out): print(c)
