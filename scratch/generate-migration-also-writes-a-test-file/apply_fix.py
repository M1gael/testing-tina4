#!/usr/bin/env python3
"""Apply the d-orm-04 text fix to a docs or book tree (argv[1]) — reference copy of the patch."""
import sys, pathlib
root = pathlib.Path(sys.argv[1])
ONLY = "Only `create_` migrations get the test. A name such as `add_category_to_product` writes just the two SQL files."
E = {
 "python": [
  ("This creates two files:\n\n```\nmigrations/000001_create_notes_table.sql\nmigrations/000001_create_notes_table.down.sql\n```\n\nThe first is your \"up\" migration. The second is the matching \"down\" migration for rollbacks.",
   "This creates three files:\n\n```\nmigrations/000001_create_notes_table.sql\nmigrations/000001_create_notes_table.down.sql\ntests/test_notes_table_migration.py\n```\n\nThe first is your \"up\" migration. The second is the matching \"down\" migration for rollbacks. The third is a test that runs the up migration and then the down migration against SQLite. " + ONLY)],
 "php": [
  ("Created migration: migrations/20260322143000_create_products_table.sql\nCreated migration: migrations/20260322143000_create_products_table.down.sql\n```\n\nThe generator creates two files: the migration itself and a matching `.down.sql` file for rollback.",
   "Created migrations/20260322143000_create_products_table.sql\nCreated migrations/20260322143000_create_products_table.down.sql\nCreated tests/ProductsTableMigrationTest.php\n```\n\nThe generator creates three files: the migration itself, a matching `.down.sql` file for rollback, and a test that runs the up migration and then the down migration against SQLite. " + ONLY)],
 "ruby": [
  ("Created migration: migrations/20260324120000_create_products_table.sql\nCreated migration: migrations/20260324120000_create_products_table.down.sql\n```\n\nThe generator creates both the up and down files.",
   "Created migrations/20260324120000_create_products_table.sql\nCreated migrations/20260324120000_create_products_table.down.sql\nCreated spec/products_table_migration_spec.rb\n```\n\nThe generator creates the up and down files plus a spec that runs the up migration and then the down migration against SQLite. " + ONLY.replace("get the test", "get the spec"))],
 "nodejs": [
  ("This creates two files in the `migrations/` folder:\n\n```\nmigrations/20260324120000_create_products_table.sql\nmigrations/20260324120000_create_products_table.down.sql\n```\n\nThe first file is the forward (up) migration. The second is the down migration used for rollbacks. Edit each one separately.",
   "This creates three files:\n\n```\nmigrations/20260324120000_create_products_table.sql\nmigrations/20260324120000_create_products_table.down.sql\ntests/products_table_migration.test.ts\n```\n\nThe first file is the forward (up) migration. The second is the down migration used for rollbacks. Edit each one separately. The third is a test that runs the up migration and then the down migration against SQLite. " + ONLY)],
}
book = {"python": "book-1-python", "php": "book-2-php", "ruby": "book-3-ruby", "nodejs": "book-4-nodejs"}
for lang, edits in E.items():
    p = root / "docs" / lang / "05-database.md"
    if not p.exists(): p = root / book[lang] / "chapters" / "05-database.md"
    s = p.read_text()
    for old, new in edits:
        assert s.count(old) == 1, (p, old[:40]); s = s.replace(old, new)
    p.write_text(s); print("edited", p)
