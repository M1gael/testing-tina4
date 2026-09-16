#!/usr/bin/env bash
# Is the skills bootstrap chain healthy, and does tina4.com serve .ps1 as text?
# Exit 0 = chain healthy AND Content-Type correct.  1 = something is wrong.
# Pinned: tina4 CLI 3.8.87, checked 2026-09-16.
set -u
fail=0

echo "== outer bootstrap (what the CLI downloads)"
for u in https://tina4.com/install-skills.ps1 \
         https://cdn.jsdelivr.net/gh/tina4stack/tina4@main/install-skills.ps1 \
         https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.ps1; do
  printf '  %-72s %s\n' "$u" "$(curl -s -o /dev/null -w '%{http_code} %{size_download}b' --max-time 25 "$u")"
done

REF=$(curl -s --max-time 25 https://tina4.com/install-skills.ps1 | grep -oE '\{ "[0-9.]+" \}' | head -1 | tr -d '{}" ')
echo "== bootstrap pins installer ref: ${REF:-UNKNOWN}"

echo "== inner installer at that ref"
for u in "https://tina4.com/skills/$REF/install-skills.ps1" \
         "https://cdn.jsdelivr.net/gh/tina4stack/tina4@$REF/install-skills.ps1" \
         "https://raw.githubusercontent.com/tina4stack/tina4/$REF/install-skills.ps1"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$u")
  printf '  %-72s %s\n' "$u" "$code"
  [ "$code" = 200 ] || fail=1
done

echo "== Content-Type on tina4.com (.htaccess half of 48716f3)"
for u in https://tina4.com/install-skills.ps1 "https://tina4.com/skills/$REF/install-skills.ps1"; do
  ct=$(curl -sI --max-time 20 "$u" | grep -i '^content-type' | tr -d '\r')
  printf '  %-56s %s\n' "${u#https://tina4.com}" "${ct:-<none>}"
  case "$ct" in *text/plain*) ;; *) echo "    ^ not text/plain: Windows PowerShell 5.1 irm returns byte[] here"; fail=1;; esac
done

[ "$fail" -eq 0 ] && { echo "OK"; exit 0; }
echo "PROBLEM"; exit 1
