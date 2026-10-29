# Applies the d-auth-02 doc fix to a docs tree (root holding docs/) or book tree (root holding book-N-*/chapters).
# usage: apply-fix.py <root> [piece...]   pieces: intro middleware toggle checklist ch33 general php37 (default: all)
import sys, pathlib, re
root = pathlib.Path(sys.argv[1]); pieces = set(sys.argv[2:]) or {"intro","middleware","toggle","checklist","ch33","general","php37"}
book = (root / "book-1-python").exists()
L = {"python":"book-1-python","php":"book-2-php","ruby":"book-3-ruby","nodejs":"book-4-nodejs"}
def f(lang, name): return root / (f"{L[lang]}/chapters/{name}" if book else f"docs/{lang}/{name}")
def sub(path, old, new, n=1):
    t = path.read_text(); c = t.count(old)
    assert c == n, f"{path}: expected {n} of {old[:60]!r}, found {c}"
    path.write_text(t.replace(old, new))
for lang in L:
    p = f(lang, "10-middleware-security.md")
    if "intro" in pieces:
        sub(p, "POST routes require authentication. CSRF tokens protect forms. Security headers harden every response.",
               "POST routes require authentication. CSRF tokens protect forms once you turn them on. Security headers harden every response.")
    if "middleware" in pieces:
        sub(p, "CSRF protection is on by default. Every POST, PUT, PATCH, and DELETE request must include a valid form token.",
               "CSRF protection is off by default. Set `TINA4_CSRF=true` to turn it on; from then on every POST, PUT, PATCH, and DELETE request must include a valid form token.")
    if "toggle" in pieces:
        t = p.read_text()
        new = ("#### Turning CSRF On\n\nCSRF stays off until you turn it on. Turn it on for anything a browser can reach:\n\n"
               "```bash\nTINA4_CSRF=true\n```\n\nThe cost is one hidden field per form. The protection is worth it. "
               "`TINA4_CSRF=false` turns it off again. Leave it off only for internal microservices behind a firewall, where no browser ever touches the API.")
        t2, k = re.subn(r"#### Disabling CSRF Globally\n\nFor internal microservices behind a firewall[^\n]*\n\n```bash\nTINA4_CSRF=false\n```\n\nLeave it enabled for anything a browser can reach\. The cost is one hidden field per form\. The protection is worth it\.", new, t)
        assert k == 1, f"{p}: toggle section not found"; p.write_text(t2)
    if "checklist" in pieces:
        sub(p, "- [ ] `TINA4_CSRF=true` (the default) for any browser-facing application.",
               "- [ ] `TINA4_CSRF=true` for any browser-facing application (CSRF is off by default).")
if "ch33" in pieces:
    for lang in ("python", "php"):
        sub(f(lang, "33-environment-variables.md"), "| `TINA4_CSRF` | `true` | CSRF token validation", "| `TINA4_CSRF` | `false` | CSRF token validation")
if "general" in pieces:
    g = root / ("book-0-understanding/chapters/04-environment-variables.md" if book else "docs/general/04-environment-variables.md")
    sub(g, "| `TINA4_CSRF` | `true` | Enable CSRF token validation on POST/PUT/PATCH/DELETE. Set to `false` to disable (e.g. for internal microservices behind a firewall). |",
           "| `TINA4_CSRF` | `false` | Enable CSRF token validation on POST/PUT/PATCH/DELETE. Set to `true` to turn it on; `false` turns it off again. |")
    sub(g, "CSRF is **on by default**. When enabled:", "CSRF is **off by default**. When enabled:")
    sub(g, "To disable for internal services:\n\n```bash\nTINA4_CSRF=false\n```", "To turn it on:\n\n```bash\nTINA4_CSRF=true\n```")
if "php37" in pieces:
    sub(f("php", "37-upgrading-from-v2.md"), "- **CSRF protection** -- Built-in, enabled by default (Chapter 10).",
           "- **CSRF protection** -- Built-in, off by default; turn it on with `TINA4_CSRF=true` (Chapter 10).")
print("applied", sorted(pieces), "to", root)
