# Does tina4-php 3.13.140 fail to extract on Windows under Composer?

Yes, for 3.13.139 and 3.13.140 only. **Windows only.** Fixed upstream in **3.13.141**, released
2026-09-29 18:13 UTC. Ledger row `f-misc-05`. Reported from Windows with 7-Zip installed:
*"3.13.138 is the last version that extracts for me without the mess."*

## Mechanism

A container build committed its PHP `conf.d` into the repo as **134 absolute symlinks** (git mode
`120000`), under `.confd_clean/`, `.confd_nogrpc/` and `.confd_withgrpc/`. Each points at
`/etc/php/8.3/cli/conf.d/*.ini`. They landed with `786d84a6` ("bump version to 3.13.139").
`.gitattributes` does not export-ignore them, so they are in the GitHub zipball that Packagist
serves as the dist.

On Windows, Composer 2.10.3 unzips with 7-Zip first when it finds `7z` on `PATH` or in
`C:\Program Files\7-Zip` (`ZipDownloader::extractWithSystemUnzip`, read). If 7z exits non-zero,
Composer falls back to ZipArchive, but only when ext-zip is loaded. Otherwise it rethrows and the
install fails.

7-Zip exits 2 on these entries for one of two reasons, depending on its version:

- **24.09 and older:** `ERROR: Dangerous link path was ignored : ...`, whatever the token. This
  is exactly the reporter's message.
- **25.01 and newer** (25.01 reworked link handling, CVE-2025-55188):
  `ERROR: Cannot create symbolic link : A required privilege is not held by the client`. This
  happens under a normal UAC-filtered terminal. Elevated, or with Developer Mode on, 7z creates
  the 134 dangling links and exits 0.

Nothing in the package reads `.confd_*`. The only reference in the 3.13.140 tree is a comment in
an export-ignored test (`tests/AppInvokeSessionCookieTest.php:30`).

## Proof

`./prove.sh` counts symlink entries in the exact dist zips. It exits 1 while a listed version
carries symlinks and 2 on an outage.

```
3.13.138: 460 entries, 0 symlinks
3.13.139: 601 entries, 134 symlinks (134 absolute)  e.g. .confd_clean/10-mysqlnd.ini -> /etc/php/8.3/cli/conf.d/10-mysqlnd.ini
3.13.140: 604 entries, 134 symlinks (134 absolute)
3.13.141: 467 entries, 0 symlinks
```

### Composer on the Windows 11 VM

Runs used PHP 8.4.25 NTS, Composer 2.10.3, a fresh project, and a fresh `COMPOSER_HOME` and
cache for each cell. `filtered` is mig's desktop session with the UAC-filtered medium token: no
`SeCreateSymbolicLinkPrivilege`, Developer Mode off. That is what a PhpStorm terminal gets.

| cell | 138 | 139 | 140 | 141 |
|---|---|---|---|---|
| no 7-Zip, ext-zip, elevated | | | rc 0, clean | |
| 7-Zip 26.03, ext-zip, elevated | rc 0 | rc 0, 134 real symlinks | rc 0, 134 real symlinks | rc 0 |
| 7-Zip 26.03, ext-zip, filtered | | | rc 0 after 134 privilege errors and the ZipArchive fallback | |
| 7-Zip 26.03, **no ext-zip**, filtered | | | **rc 1, `Install of tina4stack/tina4php failed`** | rc 0 |
| 7-Zip 24.09, ext-zip, filtered | rc 0 | rc 0 after 134 "Dangerous link path" and the fallback | same as 139 (the reporter's output) | rc 0 |
| 7-Zip 24.09, **no ext-zip**, filtered | rc 0 | | **rc 1, package not installed** | rc 0 |

With ext-zip, the fallback installs the package and leaves 134 text files whose contents are the
link targets. These are harmless. Without ext-zip, `composer.lock` is still written at 3.13.140
even though the install failed. Logs are in `evidence/`.

The 7z calls Composer makes, run directly on the 3.13.140 zip (`win/ver-matrix.ps1`):

| build | elevated | filtered |
|---|---|---|
| 7-Zip 26.03, installed and `7za` | rc 0, 134 symlinks | rc 2, 134 privilege errors |
| 7-Zip 25.01 `7za` | rc 0, 134 symlinks | rc 2, 134 privilege errors |
| 7-Zip 24.09 `7za` | rc 2, 134 "Dangerous link path" | rc 2, 134 "Dangerous link path" |

Linux 7zz 26.03 extracts the same zip with rc 0 and creates the links, so Linux is not affected.

### Re-running the Windows cells

Copy `win/*.ps1`, `composer.phar`, the 7-Zip installers or `7za.exe` builds, and `140.zip` to
`C:\Users\mig\php7z\`. Run `run-case2.ps1 -Version <v> -Label <l> [-NoZip]` for the filtered
token and `run-case.ps1` for elevated. `swap7z.ps1 -Installer <exe>` swaps the installed 7-Zip,
and `swap7z.ps1` with no argument uninstalls it. `-NoZip` needs `php-nozip.ini`, which is
`php.ini` with its `extension=zip` line removed. `limited7z.ps1` needs mig logged in on the
console (session 1).

## Upstream fix, checked

`d100bf1a` (3.13.141) removes the 134 links and adds `/.confd_*/` to `.gitignore`. It also adds
`scripts/check-no-symlinks.sh`, a `no-symlinks` CI job and a `NoSymlinksGuardTest`. The guard
returns rc 1 on the 3.13.140 tree and rc 0 on 3.13.141 (run). All 3.13.141 checks are green.

## Bounds

- Chris's 7-Zip version was not asked. His message matches 24.09 exactly (run), and 25.01+ word
  it differently. Inferred: he has 7-Zip 24.x or older.
- Composer versions other than 2.10.3 and PHP versions other than 8.4.25 were not run.
- The other ports have 0 symlinks at their 3.13.139, 3.13.140 and 3.13.141 tags (`git ls-tree`,
  run). Their dist artifacts were not inspected.
- The red CI in the report is unrelated. 3.13.139's `release-package` failed its dependency
  licence review gate. 3.13.140's `publish` crashed in "Extract this version's changelog"
  (`IndexError`), so no GitHub Release was made and Packagist was not notified. Packagist has
  3.13.140 anyway. Logs are `evidence/job-*.log`.
- Messages starting "The archive may contain identical file names with different capitalization"
  are Composer's generic hint (read). No zip here has case collisions or Windows-illegal names
  (run).

VM state was restored afterwards: 7-Zip uninstalled, the throwaway `t4probe` user and the tasks
removed, the work directory deleted, and the VM shut down.
