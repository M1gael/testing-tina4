#!/usr/bin/env bash
# Runs claims 1-6 (see readme.md). One line per claim: PASS = the claim as stated holds, FAIL = it does not,
# BROKEN = the control did not give the answer it must, so the instrument cannot be trusted for that claim.
# Ports 7650-7669 only; each is refused if busy and freed after. HOME is a temp dir for every framework run.
# Exit 0 all PASS, 1 any FAIL, 2 any BROKEN.
set -u; HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"; . ./lib.sh
RUN=$(mktemp -d); trap 'rm -rf "$RUN"' EXIT; rc=0
G=/var/home/work/gitdir/tinaforks
for t in $PYT $RBT $NDT $PHPT; do [ -d "$t" ] || { echo "missing worktree $t (see readme: setup)"; exit 2; }; done
[ -f $NDT/packages/core/dist/index.js ] || { echo "nodejs dist not built in $NDT (see readme: setup)"; exit 2; }
echo "frameworks: py $(git -C $PYT rev-parse --short HEAD) rb $(git -C $RBT rev-parse --short HEAD) nd $(git -C $NDT rev-parse --short HEAD) php $(git -C $PHPT rev-parse --short HEAD); docs $(git -C $G/tina4-documentation rev-parse --short origin/main)"
verdict(){ # verdict <n> <holds 0/1> <control ok 0/1> <evidence>
  local v; if [ "$3" != 1 ]; then v=BROKEN; rc=2; elif [ "$2" = 1 ]; then v=PASS; else v=FAIL; [ $rc = 0 ] && rc=1; fi
  echo "$v claim $1: $4"; }
hdr(){ curl -s -D - -o /dev/null --max-time 10 "$1" | tr -d '\r' | /usr/bin/grep -i "^HTTP\|^content-disposition" | sed 's/^HTTP\/1.1 //I' | tr '\n' ' '; }
nd(){ HOME=$RUN ND_TREE=$NDT node --no-warnings "$@" 2>/dev/null | tail -1; }

# ── 1. ch03 file(path, "name") on ruby and nodejs ──────────────────────────────────────────
docline(){ git -C $G/tina4-documentation show origin/main:docs/$1/03-request-response.md | /usr/bin/grep -c "file(\"/path/to/report.pdf\", \"monthly-report-march-2026.pdf\")"; }
REPORT=$RUN/report.pdf; echo '%PDF-1.4 probe' > $REPORT
r1=; c1=1; h1=0
if start_app "$(stage c1-file/rb)" 7650 REPORT=$REPORT ruby -I $RBT/lib app.rb; then
  rd=$(hdr http://127.0.0.1:7650/doc); ro=$(hdr http://127.0.0.1:7650/ok); rerr=$(/usr/bin/grep -o 'wrong number of arguments[^"]*' $APP_LOG | head -1); stop_app || c1=0
else c1=0; fi
if start_app "$(stage c1-file/nd)" 7651 REPORT=$REPORT ND_TREE=$NDT node --no-warnings app.mjs; then
  nd_d=$(hdr http://127.0.0.1:7651/doc); nd_o=$(hdr http://127.0.0.1:7651/ok); stop_app || c1=0
else c1=0; fi
# control: the real signature must give 200 + attachment on both
[[ "${ro:-}" == 200* && "$ro" == *attachment* && "${nd_o:-}" == 200* && "$nd_o" == *attachment* ]] || c1=0
# claim: the doc's 2-arg call fails on both (ruby ArgumentError -> 500; nodejs: no attachment, name dropped)
[[ "${rd:-}" == 500* && -n "${rerr:-}" && "${nd_d:-}" != *monthly-report* && "${nd_d:-}" != *attachment* && $(docline ruby) -ge 1 && $(docline nodejs) -ge 1 ]] && h1=1
verdict 1 $h1 $c1 "rb doc call -> ${rd:-?}(${rerr:-no ArgumentError}); rb file(p, download: true) -> ${ro:-?}| nd doc call -> ${nd_d:-?}(no Content-Disposition); nd file(p,{download:true}) -> ${nd_o:-?}"

# ── 2. nodejs Database.getConnection() ─────────────────────────────────────────────────────
o2=$(nd c2-getconnection.mjs)
[[ "$o2" == *control_getAdapter_same=true* ]] && c2=1 || c2=0
[[ "$o2" == *same_db=false*global_replaced=true* ]] && h2=1 || h2=0
verdict 2 $h2 $c2 "$o2"

# ── 3. nodejs createTable() before any instance ────────────────────────────────────────────
o3a=$(nd c3-columns.mjs); o3b=$(nd c3-columns.mjs instance-first)
[[ "$o3b" == *columns=id,author_id,title*rows=1* ]] && c3=1 || c3=0
[[ "$o3a" == *columns=id,authorId,title*rows=0* ]] && h3=1 || h3=0
verdict 3 $h3 $c3 "createTable first: $o3a | instance first: $o3b"

# ── 4. php ch21 Api + ch05 §3 result shape ─────────────────────────────────────────────────
port_busy 7652 && { echo "PORT 7652 BUSY"; exit 2; }
python3 c4-php/echo.py 7652 & EP=$!; for i in $(seq 40); do curl -s -o /dev/null http://127.0.0.1:7652/ping && break; sleep 0.1; done
o4=$(HOME=$RUN PHPT=$PHPT EPORT=7652 php c4-php/api.php 2>&1); kill $EP; wait $EP 2>/dev/null; wait_free 7652
g(){ echo "$o4" | /usr/bin/grep "^$1 " | cut -d' ' -f2-; }
c4=1; h4=0; DB=$RUN/db; mkdir -p $DB
[[ "$(g a_ctl_payload3rd)" == *'"body":"{\"title\":\"T\"}"'* && "$(g a_ctl_4th_is_ctype)" == *x-www-form-urlencoded* && "$(g b_ctl_get_params)" == *userId=1* \
   && "$(g c_ctl_addHeaders)" == '"v"' && "$(g d_ctl_setBasicAuth)" == '"Basic azpz"' && "$(g e_ctl_ctor_timeout_on_slow)" == "null after 1."* ]] || c4=0
if start_app "$(stage php-app)" 7653 PHPT=$PHPT TINA4_DATABASE_URL=sqlite:///$DB/app.db php $PHPT/bin/tina4php serve 127.0.0.1:7653; then
  q_doc=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7653/api/test-db); q_err=$(/usr/bin/grep -o 'Class \\"[^"]*\\" not found' $APP_LOG | head -1)
  q_fq=$(curl -s http://127.0.0.1:7653/api/test-db-fq | tr -d ' \n'); q_one=$(curl -s http://127.0.0.1:7653/api/test-db-one | tr -d ' \n'); stop_app || c4=0
else c4=0; fi
[ "${q_one:-}" = '{"answer":2}' ] || c4=0
[[ "$(g a_doc_payload4th)" == *'Argument #4 ($contentType) must be of type string, array given'* \
   && "$(g b_doc_query3rd)" == '{"query":"","body":"{\"userId\":1,\"_limit\":5}"}' \
   && "$(g c_doc_addCustomHeaders)" == *'undefined method Tina4\Api::addCustomHeaders()'* \
   && "$(g d_doc_setUsernamePassword)" == *'undefined method Tina4\Api::setUsernamePassword()'* \
   && "$(g e_doc_percall_timeout)" == *'Argument #4'* && "$(g e_percall_opts_on_slow)" == "200 after 3."* \
   && "${q_fq:-}" = '[{"answer":2}]' ]] && h4=1
verdict 4 $h4 $c4 "payload 4th: $(g a_doc_payload4th | sed 's/, called in.*//') | 3rd-arg 'query' sent as body: $(g b_doc_query3rd) | $(g c_doc_addCustomHeaders) (addHeaders -> $(g c_ctl_addHeaders)) | $(g d_doc_setUsernamePassword) (setBasicAuth -> $(g d_ctl_setBasicAuth)) | per-call {timeout:1} on 3s endpoint: $(g e_percall_opts_on_slow) vs ctor timeout 1: $(g e_ctl_ctor_timeout_on_slow); params=$(g e_sendRequest_params) | ch05 fetch -> ${q_fq:-?} (fetchOne -> ${q_one:-?}); doc's own 'use Tina4\\Database' -> $q_doc ${q_err:-}"

# ── 5. php ch33 CSRF field names ───────────────────────────────────────────────────────────
c5=1; h5=0
if start_app "$(stage php-app)" 7654 PHPT=$PHPT TINA4_CSRF=true php $PHPT/bin/tina4php serve 127.0.0.1:7654; then
  J=$RUN/jar5; curl -s -c $J -b $J -o /dev/null http://127.0.0.1:7654/login; FT=$(curl -s -c $J -b $J http://127.0.0.1:7654/ft | tr -d '\n ')
  s(){ code -c $J -b $J -d name=A "$@" http://127.0.0.1:7654/api/save; }
  n0=$(s); fb=$(s -d formToken=$FT); fh=$(s -H "X-Form-Token: $FT"); cb=$(s -d _csrf=$FT); ch=$(s -H "X-CSRF-Token: $FT"); stop_app || c5=0
else c5=0; fi
[ "${n0:-}" = 403 ] && [ "${fb:-}" = 200 ] && [ "${fh:-}" = 200 ] && [ ${#FT} -gt 100 ] || c5=0
[ "${cb:-}" = 403 ] && [ "${ch:-}" = 403 ] && git -C $G/tina4-documentation show origin/main:docs/php/33-environment-variables.md | /usr/bin/grep -q '`_csrf` in the body or `X-CSRF-Token` header' && h5=1
verdict 5 $h5 $c5 "no token $n0 | body formToken $fb, header X-Form-Token $fh | body _csrf $cb, header X-CSRF-Token $ch"

# ── 6. nodejs no-auth route still CSRF-checked ─────────────────────────────────────────────
u6=$(nd c6-csrf-unit.mjs)
c6=1; h6=0; p=7660; live=
probe6(){ local J=$RUN/jar6; rm -f $J; curl -s -c $J -b $J -o /dev/null http://127.0.0.1:$1/login; echo "$(code -d name=A http://127.0.0.1:$1/api/open) $(code -c $J -b $J -d name=A http://127.0.0.1:$1/api/save)"; }
declare -A OPEN SAVE OFF
for l in py php rb nd; do for csrf in true false; do
  case $l in py) cmd=(PYTHONPATH=$PYT $PYBIN app.py --managed); a=c6-apps/py;; rb) cmd=(ruby -I $RBT/lib app.rb); a=c6-apps/rb;;
             nd) cmd=(ND_TREE=$NDT node --no-warnings app.mjs); a=c6-apps/nd;; php) cmd=(PHPT=$PHPT php $PHPT/bin/tina4php serve 127.0.0.1:$p); a=php-app;; esac
  if start_app "$(stage $a)" $p TINA4_CSRF=$csrf "${cmd[@]}"; then read o s <<<"$(probe6 $p)"; stop_app || c6=0; else c6=0; o=x s=x; fi
  if [ $csrf = true ]; then OPEN[$l]=$o; SAVE[$l]=$s; else OFF[$l]="$o/$s"; fi; p=$((p+1)); done
  live+="$l noauth=${OPEN[$l]} (gated write ${SAVE[$l]}, CSRF off ${OFF[$l]}); "
  # control: CSRF on gates a tokenless write (403); CSRF off lets both through (200/200)
  [ "${SAVE[$l]}" = 403 ] && [ "${OFF[$l]}" = 200/200 ] || c6=0
done
[[ "$u6" == "with_route_noAuth=pass with_route_alias=pass without=403 route_noAuth_false=403" ]] || c6=0
[ "${OPEN[py]}" = 200 ] && [ "${OPEN[php]}" = 200 ] && [ "${OPEN[rb]}" = 200 ] && [ "${OPEN[nd]}" = 403 ] \
  && ! /usr/bin/grep -rqE '\.(_route|route)\s*=' $NDT/packages/core/src && h6=1
verdict 6 $h6 $c6 "beforeCsrf: $u6 | live, TINA4_CSRF=true, no token: $live"
exit $rc
