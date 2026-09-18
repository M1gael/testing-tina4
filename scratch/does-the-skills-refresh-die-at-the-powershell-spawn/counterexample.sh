#!/usr/bin/env bash
# Attack: is "zero bytes" alone enough to say the process never launched?
# Give the farm an `sh` that DOES launch and exits non-zero in silence.
set -u
here="/var/home/work/gitdir/testing-tina4/scratch/does-the-skills-refresh-die-at-the-powershell-spawn"; run="$here/run"; farm="$run/farm"
cp /usr/bin/false "$farm/sh"
home="$run/home-C"; rm -rf "$home"; mkdir -p "$home"
PATH="$farm" HOME="$home" "$here/tina4-3.8.88-stock" skills all >"$run/C.out" 2>"$run/C.err"
echo "exit=$?"
sed 's/^/  | /' "$run/C.out"; sed 's/^/  E /' "$run/C.err"
echo "stdout=$(wc -c <"$run/C.out")b stderr=$(wc -c <"$run/C.err")b"
diff -q "$run/A.out" "$run/C.out" >/dev/null && echo "C.out IDENTICAL to A.out (spawn-failure arm)" || echo "C.out differs from A.out"
