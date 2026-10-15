# Does the documented PHP Composer package exist? (d-pkg-01, f-pkg-02)

No. `tina4stack/tina4-php` (hyphen) was never a Composer package: Packagist p2 and packages.json both 404,
and php's `composer.json` has always been `tina4stack/tina4php`. The hyphenated name is right for the GitHub
repo and the Docker image only. Reported in tina4-documentation issue 142.

Wrong Composer references (tips: docs `dc1d5b8`, book `15ef833`, php v3 `82654f83`, tina4 `main`):
- docs `docs/php/36-releases.md`, `37-upgrading-from-v2.md`, `docs/v2/php/php-on-{mac,windows}.md`;
  book `book-2-php/chapters/36-releases.md`, `37-upgrading-from-v2.md` (the book is the source: `scripts/sync-books.sh`).
- php `bin/tina4php` `init` writes `"tina4stack/tina4-php": "^3.0"`, so `composer install` fails:
  "Root composer.json requires tina4stack/tina4-php, it could not be found in any version". Dev-admin's
  patch-update hint (`Tina4/DevAdmin.php:3466`) names the same package.
- tina4 CLI `src/install.rs:286` hint; `scripts/RELEASING-FRAMEWORKS.md:166,345` Packagist check URL.
  (`tina4 init` in `src/init.rs:693` and `upgrade.rs` are already right.)

`check.sh <tree>`: every tina4stack package the docs tell readers to require must exist on Packagist.
Fails on stock docs and book, passes fixed (`check.out`).
Patches: `~/.cache/tina4-worktrees/{doc142-docs,doc142-book,pkgname-php,pkgname-cli}.fix.patch`.
Left alone: generated PDFs, frozen `docs/public/skills/version/...` bundles, Docker/GitHub refs.
Noticed: `docs/php/36-releases.md` (and the book) have the v3.10.70 section pasted repeatedly, once inside the
v2→v3 bash block (lines ~4420-5290).
