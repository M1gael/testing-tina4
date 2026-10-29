#!/usr/bin/env bash
# d-cli-03: do the docs/book describe `tina4 build` as what it is (SCSS + docker build)?
# Usage: DOCS=<docs tree root> BOOK=<book tree root> ./prove.sh   (either may be omitted)
# rc 0 = PASS, rc 1 = wrong or missing text found.
set -u
here=$(cd "$(dirname "$0")" && pwd)
exec python3 -I "$here/check_docs.py" "${DOCS:--}" "${BOOK:--}"
