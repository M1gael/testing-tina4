#!/bin/sh
# What does a user get who runs `tina4 init python|ruby` on iSH WITHOUT the apk repo switch?
# Fresh rootfs per profile: appstore (App Store engine + Alpine 3.14) and testflight
# (master engine + Alpine 3.19).  Usage: PROFILE=appstore|testflight ish-noswitch-init.sh
set -u
VM=/var/home/work/vm; D=$VM/ios; P=${PROFILE:-appstore}
case $P in appstore) TAR=alpine-minirootfs-3.14.10-x86.tar.gz; ENG=$D/src-appstore/build ;;
           testflight) TAR=alpine-minirootfs-3.19.9-x86.tar.gz; ENG=$D/src/build ;; esac
ROOT=noswitch-$P
rm -rf "$D/$ROOT"
"$ENG/tools/fakefsify" "$D/dl/$TAR" "$D/$ROOT"
"$ENG/ish" -f "$D/$ROOT" /bin/sh -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf'
run() { echo "### $1"; ISH=$P ISH_ROOT=$ROOT "$VM/ish.sh" "$1" 2>&1 | tail -${2:-15}; }
run 'cat /etc/alpine-release; uname -r'
run 'apk add curl' 2
run 'curl -fsSL https://tina4.com/install.sh | sh' 3
run 'tina4 --version'
run 'cd /root && timeout 1800 tina4 init python app-py </dev/null; echo init-rc=$?; python3 --version; ls app-py 2>&1 | head -5' 25
run 'cd /root && timeout 1800 tina4 init ruby app-rb </dev/null; echo init-rc=$?; ruby --version; ls app-rb 2>&1 | head -5' 25
run 'cd /root/app-py 2>/dev/null && timeout 120 tina4 serve </dev/null & sleep 60; wget -qO- http://localhost:7146/ 2>&1 | head -3; echo serve-probe-done; kill %1 2>/dev/null' 12
rm -rf "$D/$ROOT"
