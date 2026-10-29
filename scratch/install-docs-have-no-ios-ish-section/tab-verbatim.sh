#!/bin/sh
# Run the index page's iOS tab VERBATIM (as extracted from DOCS) on a fresh rootfs, then init
# python and ruby. `tina4 setup` needs a tty, so it is replaced by the two inits it would lead to.
# Usage: DOCS=<docs root> PROFILE=appstore|testflight tab-verbatim.sh
set -u
VM=/var/home/work/vm; D=$VM/ios; P=${PROFILE:-appstore}
case $P in appstore) TAR=alpine-minirootfs-3.14.10-x86.tar.gz; ENG=$D/src-appstore/build ;;
           testflight) TAR=alpine-minirootfs-3.19.9-x86.tar.gz; ENG=$D/src/build ;; esac
TAB=$(sed -n '/== iOS (iSH/,/^```$/p' "$DOCS/docs/index.md" | sed '1,2d;$d' | grep -v '^tina4 setup$')
echo "## tab commands:"; echo "$TAB"
ROOT=tabverb-$P; rm -rf "$D/$ROOT"
"$ENG/tools/fakefsify" "$D/dl/$TAR" "$D/$ROOT"
"$ENG/ish" -f "$D/$ROOT" /bin/sh -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf'
run() { echo "### $1"; ISH=$P ISH_ROOT=$ROOT "$VM/ish.sh" "$1" 2>&1 | tail -${2:-6}; }
run 'cat /etc/alpine-release' 1
run "set -e; $(echo "$TAB" | tr '\n' ';') echo tab-rc=0" 4
run 'cat /etc/alpine-release; tina4 --version' 2
run 'cd /root && timeout 1800 tina4 init python app-py </dev/null; echo init-py-rc=$?; app-py/.venv/bin/python --version' 4
run 'cd /root && timeout 1800 tina4 init ruby app-rb </dev/null; echo init-rb-rc=$?; ruby --version' 4
rm -rf "$D/$ROOT"
