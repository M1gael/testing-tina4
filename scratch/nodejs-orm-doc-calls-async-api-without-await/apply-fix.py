# usage: apply-fix.py <docs-worktree> <book-worktree>
# Applies the d-orm-01 edits (adds the missing awaits) to both trees and checks each edit's count.
import re, sys, pathlib
docs, book = map(pathlib.Path, sys.argv[1:3])

def edit(path, pairs):
    p = pathlib.Path(path); s = p.read_text()
    for pat, rep, n in pairs:
        s, k = re.subn(pat, rep, s, flags=re.M)
        if n is not None and k != n: sys.exit(f"{p}: {pat!r} matched {k}, expected {n}")
    p.write_text(s)

GETCONN = [(r"(=\s*)Database\.getConnection\(\)", r"\1await Database.getConnection()", None)]
CH06 = [(r"= Note\.create\(\{", "= await Note.create({", 1),
        (r"= (\w+)\.(hasMany|belongsTo|hasOne)\(", r"= await \1.\2(", 8),
        (r"= BlogPost\.published\(\);", "= await BlogPost.published();", 2),
        (r"= \(BlogPost as any\)\.active\(", "= await (BlogPost as any).active(", 2)]
CH07 = [(r"const total = qb\.count\(\);", "const total = await qb.count();", 1),
        (r"const products = qb$", "const products = await qb", 1),
        (r'const results = qb\.orderBy\("revenue DESC"\)\.get\(\);', 'const results = await qb.orderBy("revenue DESC").get();', 1)]
CH26 = [(r'const (db[12]) = container\.get\("db"\);', r'const \1 = await container.get("db");', 2),
        (r'^app\.singleton\("db", \(\) => Database\.getConnection\(\)\);',
         'const db = await Database.getConnection();\napp.singleton("db", () => db);', 1)]
CH29 = [(r"^function testLookupCustomer\(\) \{\n  const result = db\.fetchOne\(",
         "async function testLookupCustomer() {\n  const result = await db.fetchOne(", 1),
        (r"\]\)\(\(args\) => \{\n  db\.execute\(", "])(async (args) => {\n  await db.execute(", 1)]
CH18 = [(r"^function testDeleteProduct\(\): boolean \{\n    const product = new Product\(\{ name: \"Temporary\", price: 1 \}\);\n    product\.save\(\);\n    product\.delete\(\);\n    return Product\.findById\(product\.id\) === null;",
         "async function testDeleteProduct(): Promise<boolean> {\n    const product = new Product({ name: \"Temporary\", price: 1 });\n    await product.save();\n    await product.delete();\n    return (await Product.findById(product.id)) === null;", 1),
        (r"^function testDeleteProduct\(\): boolean \{\n    const product = Product\.findById\(1\); // Assumes ID 1 exists\n    product\.delete\(\);",
         "async function testDeleteProduct(): Promise<boolean> {\n    const product = await Product.findById(1); // Assumes ID 1 exists\n    await product.delete();", 1),
        (r"^function testCreateUser\(\): boolean \{\n(    const email = .*\n    const user = .*\n)    user\.save\(\);",
         r"async function testCreateUser(): Promise<boolean> {\n\1    await user.save();", 1)]
CHOOSE = [(r"^export default function handler\(request, response\) \{\n    const (products|product) = Product\.(select|create)\(",
           r"export default async function handler(request, response) {\n    const \1 = await Product.\2(", 2)]

for root, sub in ((docs, "docs/nodejs"), (book, "book-4-nodejs/chapters")):
    d = root / sub
    for f in sorted(d.glob("*.md")):
        if f.name == "36-releases.md": continue
        edit(f, GETCONN)
    edit(d / "06-orm.md", CH06); edit(d / "07-query-builder.md", CH07); edit(d / "26-di-container.md", CH26)
    edit(d / "29-custom-mcp-servers.md", CH29); edit(d / "18-testing.md", CH18)
edit(docs / "docs/general/03-choosing-your-language.md", CHOOSE)
edit(book / "book-0-understanding/chapters/03-choosing-your-language.md", CHOOSE)
edit(docs / "docs/general/frond.md", [(r"\{ rows: Price\.all\(\) \}\);   // Node", "{ rows: await Price.all() });   // Node", 1)])
print("applied")
