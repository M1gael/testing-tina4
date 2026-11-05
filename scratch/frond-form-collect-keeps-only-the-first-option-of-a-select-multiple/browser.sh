#!/bin/sh
# Usage: browser.sh <dir holding frond.js>  — same select-multiple cell in headless Chromium.
set -e
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
cp "$1/frond.js" "$T/frond.js"
cat > "$T/p.html" <<'H'
<!doctype html><body><form id="f"><select multiple name="g[]"><option value="1" selected>A</option><option value="2" selected>B</option><option value="3">C</option><option value="4" selected disabled>D</option><optgroup disabled><option value="5" selected>E</option></optgroup></select><select multiple name="none[]"><option value="9">Z</option></select></form>
<pre id="out"></pre><script src="frond.js"></script><script>
const f=document.getElementById("f");
document.getElementById("out").textContent="collect="+JSON.stringify([...frond.form.collect("f").entries()])+" native="+JSON.stringify([...new FormData(f).entries()]);
</script></body>
H
chromium --headless=new --no-sandbox --disable-gpu --user-data-dir="$T/prof" --allow-file-access-from-files --dump-dom "file://$T/p.html" 2>/dev/null | grep -o 'collect=.*native=[^<]*'
