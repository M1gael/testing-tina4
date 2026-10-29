#!/bin/sh
# Runs the patch's iOS (iSH) Get Started commands verbatim on a FRESH App Store
# engine + Alpine 3.14 rootfs (no curl), then probes each language's init.
# Usage: ISH=appstore scratch/install-docs-have-no-ios-ish-section/ish-run.sh  (default appstore)
# Rootfs lives in vm/ios/$ISH_ROOT (default dsite03-<profile>); output to stdout.
set -u
VM=/var/home/work/vm; D=$VM/ios
PROFILE=${ISH:-appstore}; ROOT=${ISH_ROOT:-dsite03-$PROFILE}
case $PROFILE in appstore) V=3.14.10 ;; testflight) V=3.19.9 ;; *) echo "profile $PROFILE not covered"; exit 2 ;; esac
rm -rf "$D/$ROOT"
"$D/src/build/tools/fakefsify" "$D/dl/alpine-minirootfs-$V-x86.tar.gz" "$D/$ROOT"
"$D/src/build/ish" -f "$D/$ROOT" /bin/sh -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf'
run() { echo "### $1"; ISH=$PROFILE ISH_ROOT=$ROOT "$VM/ish.sh" "$1" 2>&1 | tail -${2:-15}; echo "### rc=$?"; }
run 'cat /etc/alpine-release; uname -m -r; command -v curl || echo "no curl"'
# --- the docs block, verbatim ---
run "printf '%s\n' https://dl-cdn.alpinelinux.org/alpine/latest-stable/main https://dl-cdn.alpinelinux.org/alpine/latest-stable/community > /etc/apk/repositories" 5
run 'apk upgrade --available' 4
run 'apk add curl' 3
run 'curl -fsSL https://tina4.com/install.sh | sh' 15
# --- what the text says about the result ---
run 'cat /etc/alpine-release; ls -l /usr/local/bin/tina4; tina4 --version; file /usr/local/bin/tina4 2>/dev/null || head -c 20 /usr/local/bin/tina4 | od -c | head -2' 8
for L in php nodejs; do run "cd /root && tina4 init $L app-$L; echo init-rc=\$?; ls app-$L 2>&1 | head -3; apk info 2>/dev/null | grep -cE '^(php|nodejs|npm|composer)' " 8; done
run 'cd /root && timeout 1800 tina4 init python app-py; echo init-rc=$?; ls -d app-py/.venv && app-py/.venv/bin/pip --version; command -v uv || echo no-uv' 25
run 'cd /root && timeout 1800 tina4 init ruby app-rb; echo init-rc=$?; ruby --version; ls app-rb | head' 15
