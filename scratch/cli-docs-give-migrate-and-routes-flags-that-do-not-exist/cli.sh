#!/usr/bin/env bash
# usage: cli.sh <py|php|rb|nd> <args...>
# Runs that port's framework CLI from a worktree at the upstream v3 tip -- what `tina4 <args>` forwards
# to verbatim (tina4 src/main.rs:314-323, :526, delegate_command :1787).
# Worktrees live outside scratch/ (never put framework copies here); override with TINA4_PY/PHP/RB/ND.
W=${TINA4_WT:-${HOME_REAL:-$HOME}/.cache/tina4-worktrees}
f=$1; shift
case $f in
  py)  PYTHONPATH=${TINA4_PY:-$W/dcli04-stock-python} exec python3 -c 'import sys; from tina4_python.cli import main; sys.argv[0]="tina4python"; main()' "$@";;
  php) exec php ${TINA4_PHP:-$W/dcli04-stock-php}/bin/tina4php "$@";;
  rb)  R=${TINA4_RB:-$W/dcli04-stock-ruby}; exec ruby -I $R/lib $R/exe/tina4ruby "$@";;
  nd)  exec node ${TINA4_ND:-$W/dcli04-stock-nodejs}/packages/cli/dist/bin.js "$@";;
  *)   echo "usage: cli.sh <py|php|rb|nd> <args...>" >&2; exit 2;;
esac
