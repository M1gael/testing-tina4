#!/bin/sh
# The index page's iOS (iSH) tab, verbatim, on a FRESH App Store engine + Alpine 3.14
# rootfs (no repo switch), then `tina4 install python|ruby` (setup needs a tty) to see
# what a user who only read the tab gets.  Usage: ish-tab-run.sh  > ish-tab-run.log
set -u
VM=/var/home/work/vm; D=$VM/ios; ROOT=dsite03-tab
rm -rf "$D/$ROOT"
"$D/src/build/tools/fakefsify" "$D/dl/alpine-minirootfs-3.14.10-x86.tar.gz" "$D/$ROOT"
"$D/src/build/ish" -f "$D/$ROOT" /bin/sh -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf'
run() { echo "### $1"; ISH=appstore ISH_ROOT=$ROOT "$VM/ish.sh" "$1" 2>&1 | tail -${2:-15}; }
run 'cat /etc/alpine-release; uname -r'
run 'apk add curl' 3
run 'curl -fsSL https://tina4.com/install.sh | sh' 12
run 'tina4 --version; tina4 setup </dev/null; echo setup-rc=$?' 6
run 'timeout 900 tina4 install python; echo rc=$?' 14
run 'timeout 900 tina4 install ruby; echo rc=$?' 14
run 'timeout 300 tina4 install php; echo rc=$?' 6
