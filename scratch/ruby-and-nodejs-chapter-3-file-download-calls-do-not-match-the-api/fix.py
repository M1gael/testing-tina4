# fix.py <docs-tree> <book-tree> [SKIP=<piece>] -- rewrites ruby and nodejs chapter 3 file() examples to the real API.
# Pieces: 1 ruby file(path, download: true) + prose; 2 ruby paths without ".."; 4 ruby `next` not `return` in the route block; 3 nodejs file(path, {download: true}) + prose.
import os, pathlib, sys

skip = os.environ.get("SKIP", "")
docs, book = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

RUBY = {
    "1": [
        ("Send a file for download:\n", "Send a file:\n"),
        ("Tina4 sets the right `Content-Type` from the file extension and adds `Content-Disposition` so the browser downloads instead of displaying.\n\nCustom filename:\n",
         "Tina4 sets the right `Content-Type` from the file extension. Pass `content_type:` to override it.\n\nForce a download (`Content-Disposition: attachment`, saved under the file's own name):\n"),
        ('response.file("/path/to/report.pdf", "monthly-report-march-2026.pdf")\n```\n\nThis sets the `Content-Disposition: attachment` header with your chosen filename.\n',
         'response.file("/path/to/report.pdf", download: true)\n```\n'),
        ("The browser downloads the file. Tina4 detects the MIME type from the extension and sets the right headers.\n",
         "Tina4 detects the MIME type from the extension and sets the right headers.\n"),
        ('Force a specific download filename:\n\n```ruby\nresponse.file(filepath, "Q1-2026-Sales-Report.pdf")\n',
         "Force a download (the browser saves it under the file's own name):\n\n```ruby\nresponse.file(filepath, download: true)\n"),
    ],
    "2": [
        ('filepath = File.join(__dir__, "../../data/reports", filename)', 'filepath = File.join(Dir.pwd, "data/reports", filename)'),
        ("Tina4 detects the MIME type from the extension and sets the right headers.\n",
         "Tina4 detects the MIME type from the extension and sets the right headers. A path containing a `..` segment is refused with `403`, so build it from `Dir.pwd` (the project root) rather than `File.join(__dir__, \"../..\")`.\n"),
        ('filepath = File.join(__dir__, "../public/uploads", filename)', 'filepath = File.join(Dir.pwd, "src/public/uploads", filename)'),
    ],
    "4": [
        ('    return response.json({ error: "Report not found" }, 404)\n', '    next response.json({ error: "Report not found" }, 404)\n'),
    ],
}
NODE = {
    "3": [
        ("Send a file to the client for download:\n", "Send a file to the client:\n"),
        ("Tina4 sets the appropriate `Content-Type` based on the file extension and adds a `Content-Disposition` header so the browser downloads the file.\n\nSet a custom filename:\n",
         "Tina4 sets the appropriate `Content-Type` based on the file extension. Pass `{ contentType }` to override it.\n\nForce a download (`Content-Disposition: attachment`, saved under the file's own name):\n"),
        ('return res.file("/path/to/report.pdf", "monthly-report-march-2026.pdf");', 'return res.file("/path/to/report.pdf", { download: true });'),
        ("To force a specific download filename:\n", "To force a download (the browser saves it under the file's own name):\n"),
        ('return res.file(filepath, "Q1-2026-Sales-Report.pdf");', "return res.file(filepath, { download: true });"),
    ],
}


def apply(path, pieces):
    s = path.read_text()
    for k, subs in pieces.items():
        if k == skip:
            continue
        for a, b in subs:
            if s.count(a) != 1:
                raise SystemExit(f"{path}: piece {k}: expected 1 match, got {s.count(a)}: {a[:60]!r}")
            s = s.replace(a, b)
    path.write_text(s)


for p in (docs / "docs/ruby/03-request-response.md", book / "book-3-ruby/chapters/03-request-response.md"):
    apply(p, RUBY)
for p in (docs / "docs/nodejs/03-request-response.md", book / "book-4-nodejs/chapters/03-request-response.md"):
    apply(p, NODE)
print("applied", "all" if not skip else f"all but piece {skip}")
