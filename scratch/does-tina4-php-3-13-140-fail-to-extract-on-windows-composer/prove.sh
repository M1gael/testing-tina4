#!/usr/bin/env bash
# Does the Composer dist of tina4stack/tina4php carry symlink entries?
# Downloads the exact zip Packagist points Composer at, per version, and counts
# symlink entries (unix mode S_IFLNK in the zip's external attributes).
#
#   ./prove.sh                      # 3.13.138 3.13.139 3.13.140 3.13.141
#   ./prove.sh 3.13.140             # one version
#
# Exit 0: every version listed is clean.  Exit 1: at least one carries symlinks.
# Exit 2: Packagist or GitHub could not be reached; nothing was measured.
set -u
versions=${*:-3.13.138 3.13.139 3.13.140 3.13.141}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
if ! curl -sf https://repo.packagist.org/p2/tina4stack/tina4php.json -o "$tmp/meta.json"; then
  echo "SKIP: packagist metadata unreachable"; exit 2
fi
status=0
for v in $versions; do
  url=$(python3 -c "import json,sys; d=json.load(open('$tmp/meta.json'))['packages']['tina4stack/tina4php']; print(next((x['dist']['url'] for x in d if x['version']=='$v'), ''))")
  [ -z "$url" ] && { echo "$v: not on Packagist"; status=1; continue; }
  code=$(curl -sL -o "$tmp/$v.zip" -w '%{http_code}' "$url")
  [ "$code" = 200 ] || { echo "SKIP: $v dist download returned $code"; exit 2; }
  python3 - "$tmp/$v.zip" "$v" <<'EOF' || status=1
import stat, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
links = [i for i in z.infolist() if stat.S_ISLNK(i.external_attr >> 16)]
absolute = [i for i in links if z.read(i).startswith(b'/')]
first = f"  e.g. {links[0].filename.split('/', 1)[1]} -> {z.read(links[0]).decode()}" if links else ''
print(f"{sys.argv[2]}: {len(z.infolist())} entries, {len(links)} symlinks ({len(absolute)} absolute){first}")
sys.exit(1 if links else 0)
EOF
done
exit $status
