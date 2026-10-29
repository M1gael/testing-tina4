#!/usr/bin/env python3
"""Revert ONE component of the Termux change, build that tree for x86_64 Android,
and restore the source byte-for-byte. Prints the path of the mutant binary.

usage: mutate.py <worktree> <mutation-name> <out-binary>
"""
import os, shutil, subprocess, sys

WT, NAME, OUT = sys.argv[1:4]

# name -> (file, text in the patched tree, replacement that undoes only that piece)
MUTATIONS = {
    "init-runtime": ("src/init.rs",
        "    if console::is_android() {\n        if !crate::install::termux_install(crate::install::termux_packages(label)) {",
        "    if false {\n        if !crate::install::termux_install(crate::install::termux_packages(label)) {"),
    "init-uv": ("src/init.rs",
        "                let ok = if console::is_android() {\n                    crate::install::termux_install(&[\"uv\"])",
        "                let ok = if false {\n                    crate::install::termux_install(&[\"uv\"])"),
    "init-composer": ("src/init.rs",
        "                } else if console::is_android() {\n                    if !crate::install::termux_install(&[\"composer\"]) {",
        "                } else if false {\n                    if !crate::install::termux_install(&[\"composer\"]) {"),
    "ruby-build-config": ("src/install.rs",
        "pub fn termux_ruby_build_config() {\n",
        "pub fn termux_ruby_build_config() {\n    return;\n"),
    "install-php": ("src/install.rs",
        "    } else if console::is_android() {\n        termux_install(termux_packages(\"php\"));",
        "    } else if false {\n        termux_install(termux_packages(\"php\"));"),
    "install-composer": ("src/install.rs",
        "        } else if console::is_android() {\n            // getcomposer.org's installer",
        "        } else if false {\n            // getcomposer.org's installer"),
    "install-ruby": ("src/install.rs",
        "    } else if console::is_android() {\n        termux_install(termux_packages(\"ruby\"));",
        "    } else if false {\n        termux_install(termux_packages(\"ruby\"));"),
    "install-node": ("src/install.rs",
        "    } else if console::is_android() {\n        termux_install(termux_packages(\"nodejs\"));",
        "    } else if false {\n        termux_install(termux_packages(\"nodejs\"));"),
    "local-bin-path": ("src/install.rs",
        "    if console::is_android() {\n        termux_local_bin_on_path();",
        "    if false {\n        termux_local_bin_on_path();"),
    "uv-link-mode": ("src/main.rs",
        "    if console::is_android() && std::env::var_os(\"UV_LINK_MODE\").is_none() {",
        "    if false && std::env::var_os(\"UV_LINK_MODE\").is_none() {"),
    "libsqlite-header": ("src/install.rs",
        "    if !header {\n        termux_install(&[\"libsqlite\"]);",
        "    if false && !header {\n        termux_install(&[\"libsqlite\"]);"),
    "setup-git": ("src/setup.rs",
        "    } else if console::is_android() {\n        crate::install::termux_install(&[\"git\"])",
        "    } else if false {\n        crate::install::termux_install(&[\"git\"])"),
}

path, old, new = MUTATIONS[NAME]
full = os.path.join(WT, path)
original = open(full, "rb").read()
text = original.decode()
assert text.count(old) == 1, f"{NAME}: anchor found {text.count(old)} times"
try:
    open(full, "w").write(text.replace(old, new))
    env = dict(os.environ,
               PATH=os.path.expanduser("~/.cargo/bin") + ":" + os.environ["PATH"],
               ANDROID_NDK_HOME="/var/home/work/vm/android/sdk/ndk/27.2.12479018",
               CARGO_TARGET_DIR=os.path.expanduser("~/.cache/tina4-worktrees/android-cli-mutant-target"))
    r = subprocess.run(["cargo", "ndk", "-t", "x86_64", "-P", "24", "build", "--release", "--locked"],
                       cwd=WT, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])
    shutil.copy(os.path.join(env["CARGO_TARGET_DIR"], "x86_64-linux-android/release/tina4"), OUT)
finally:
    open(full, "wb").write(original)
assert open(full, "rb").read() == original
print(OUT)
