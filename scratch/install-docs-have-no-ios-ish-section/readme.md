# install docs have no iOS (iSH) section — ledger d-site-03

Rebuilt 2026-10-29 on docs origin/main 01c4225 and tina4 CLI ebb846b (= release v3.8.112,
which is what the hosted install.sh fetched under iSH). Held fix:
`~/.cache/tina4-worktrees/ios-docs.fix.patch` (made on docs b120ab1). Docs-only row, no book patch.

Trees (outside scratch): `~/.cache/tina4-worktrees/verify-1029/dsite03/{stock,fixed}` —
`git archive 01c4225`, fixed = stock + `git apply` of the patch (applies clean; index.md hunk
offset -12).

- `prove.sh` (`DOCS=<tree>`): every .md under docs/ except docs/public; iSH named on the four
  install pages, apk repo switch present, languages stated, docs/public/install.sh == CLI tip.
  stock: `pages_with_iSH=0/4 apk_switch=0 languages_stated=0 install.sh=equal` rc 1;
  fixed: `4/4 1 1 equal` rc 0. install.ps1 differs from the tip (stale since CLI #126, f-cli-60);
  the patch does not touch it.
- `build.sh` (`DOCS=<tree>`): tina4press build (node_modules from verify-1028/nm), checks the tab
  and the three sections in dist. fixed: 283 pages, 5/5 present; stock: 0/5.
- `ish-run.sh` (ISH=appstore): fresh App Store engine + Alpine 3.14 rootfs, no curl; runs the
  Get Started block verbatim, then init php/nodejs (refused, 0 packages) and python/ruby (both
  created; Python .venv with pip, no uv; Python 3.14, Ruby 3.4). Log `ish-run-appstore.log`.
- `ish-tab-run.sh`: the index tab only (no repo switch) on Alpine 3.14: install works, then
  `tina4 install python|ruby` installs 3.9 / 2.7 and prints the repo switch. Log `ish-tab-run.log`.
- `ish-warning-check.log`: the "iOS (iSH) support is experimental." warning (src/install.rs:930).

Rootfs dirs `vm/ios/dsite03-*` are deleted after the runs; the scripts recreate them.
