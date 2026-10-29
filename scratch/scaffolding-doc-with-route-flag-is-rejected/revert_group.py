"""Put one hunk group of the held fix back to its stock text, in all 8 files."""
import sys, glob
grp, d, b = sys.argv[1:4]
TABLE = ("Available flags:\n\n| Flag | Adds |\n|------|------|\n| `--with-route` | CRUD route file |\n"
         "| `--with-migration` | Migration files (included by default with model) |\n"
         "| `--with-test` | Test file |\n| `--with-form` | Form template |\n| `--with-view` | View templates |")
def block(cli):
    return (f'{cli} generate model Product --fields "name:string,price:float"\n{cli} generate route products --model Product\n',
            f'{cli} generate model Product --fields "name:string,price:float" --with-route --with-migration\n')
for f in glob.glob(f"{d}/docs/*/19-scaffolding.md") + glob.glob(f"{b}/book-*/chapters/19-scaffolding.md"):
    s = open(f).read()
    cli = "tina4python" if "python" in f else "tina4"
    pairs = {
        "intro": ("Run the individual generators one after another. Each adds one piece:",
                  "Or a model with a migration but no test. The `--with` flags let you compose:"),
        "block": block(cli),
        "table": ("`generate model` writes the migration by default. Pass `--no-migration` to leave it out. "
                  "Add `generate form`, `generate view` or `generate test` for the other pieces.", TABLE),
        "crud": ("builds the full set in one step.", "is equivalent to using all `--with` flags at once."),
    }
    old, new = pairs[grp]
    if s.count(old) != 1:
        sys.exit(f"{f}: fixed text for {grp} found {s.count(old)} times")
    open(f, "w").write(s.replace(old, new))
