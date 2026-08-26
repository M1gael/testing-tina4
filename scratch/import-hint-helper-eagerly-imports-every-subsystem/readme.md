# import-hint-helper-eagerly-imports-every-subsystem

**The 3.13.117 import-hint helper imports every optional subsystem when `tina4_python` is
imported, and that silently turns `realtime` from a callable into a module.**

Ledger row: `f-imp-01`. Not our defect — introduced upstream in `2e55627`
(*feat(cli): import-hint fallback for wrong-guess `tina4_python.<X>` imports*, Andre van
Zuydam, 2026-08-25) and released the same day as **3.13.117**.

Pinned to `tina4-python` `origin/v3` @ `a4d524c`, `_import_helper.py` md5
`9fd47dead99eacb6bc3b2b7661616c8a`.

## Run it

```bash
./prove.sh                 # builds a detached worktree at origin/v3 and probes it
./prove.sh /path/to/repo   # or probe a checkout you already have
```

Each arm runs in its own interpreter: the defect is about what a single
`import tina4_python` does, so it cannot be measured twice in one process.

## Mechanism

`tina4_python/__init__.py:232` installs the helper at package-import time:

```python
from tina4_python._import_helper import install as _install_import_helper
_install_import_helper()
```

`install()` constructs `_Tina4ModuleFinder`, whose `__init__` snapshots the module tree
(`_import_helper.py:37`) via `_walk()`, which at `:44` reads:

```python
name for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix=_PREFIX)
```

**`pkgutil.walk_packages` imports every package it descends into.** It has to: to recurse into
a subpackage it needs that package's `__path__`, and the only way to get it is to import the
package. `pkgutil.iter_modules` does not — that is the whole difference between the two.

The docstring says the suggestion list is *"derived from the REAL installed tree
(pkgutil.walk_packages)"*, and for producing names that is true. The side effect is the
problem, and it is not visible at the call site.

### Two consequences, one cause

**1. The lazy subsystem loading is defeated.** 20 optional modules load on a bare
`import tina4_python` — `crud`, `docstore`, `graphql`, `messenger`, `mqtt`, `queue` and its
five backends, `seeder`, `swagger`, `wsdl`. That is what
`tests/test_lazy_feature_loading.py` asserts against, and it is the visible half.

**2. The public `realtime()` API stops being callable — the half that reaches users.**
`__init__.py:166` maps the lazy attribute to the *function* inside the subpackage:

```python
"realtime": ("tina4_python.realtime", "realtime"),
```

`__getattr__` only runs when a real attribute is absent. Importing `tina4_python.realtime`
binds the **module** as an attribute on the parent package, so `__getattr__` is never
consulted again and `tina4_python.realtime` is the module. Calling it raises
`TypeError: 'module' object is not callable`.

This is the same shape as the `websocket` defect fixed in 3.13.106 (`PY-FW-03`), reached by a
different route: there the subpackage name shadowed the decorator, here an unrelated feature
imports the subpackage and creates the shadow as a side effect.

## Before / after

```
=== ARM 1 — stock: the helper installs and walks ===
    eager optional subsystems : 20
    tina4_python.realtime     : module, callable=False

=== ARM 2 — same tree, the eager walk neutralised (nothing else changed) ===
    eager optional subsystems : 0
    tina4_python.realtime     : function, callable=True
```

One variable changed. `realtime` crosses from module to function with it.

## Blast radius in the test suite

19 of the 20 failures on upstream `v3` @ `a4d524c` are this one bug:

| tests | count | which half |
|---|---|---|
| `test_realtime_chat.py`, `test_realtime_files.py` | 14 errors | `realtime()` not callable |
| `test_realtime_signalling.py` | 3 failed | same |
| `test_lazy_feature_loading.py` | 2 failed | eager imports |

The 20th, `test_version_consistency.py::test_claude_md_version_matches_pyproject`, is
unrelated: `CLAUDE.md` still carries a `3.13.116` footer after the 3.13.117 release.

## The fix

Enumerate the tree from **disk**, never through the import system.

`pkgutil.iter_modules` is not sufficient on its own — it lists only the top level, and the
feature's own test (`tests/test_import_helper.py:89`) requires the nested
`tina4_python.core.router` to appear in the hint. A filesystem walk gives 114 names including
nested ones, with `iter_modules` kept as a non-importing fallback for zipimport and namespace
packages.

**The other three ports already do it correctly, which is the strongest argument for this
shape of fix:** tina4-php enumerates with `RecursiveDirectoryIterator`
(`Tina4/ImportHelper.php:225`), tina4-ruby reads `Tina4.constants`
(`lib/tina4/import_helper.rb:123`), and tina4-nodejs reads its own `package.json` exports map
at throw time (`f316e16`). None of them loads anything to build the list. Python is the only
port that does, and it is the only port where the feature broke an API.
