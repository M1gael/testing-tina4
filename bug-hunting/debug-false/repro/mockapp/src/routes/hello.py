"""The one hand-written route in this app.

It is a SINGLE route with a path parameter — ``/hello/{page}`` — deliberately,
not two separate routes. That keeps the router table at exactly 99 entries
(19 AutoCRUD models x 5 = 95, plus this one, plus the 3 the framework
registers itself) so the dev footer reads the same number as the bug report,
while still giving you two URLs to click between.

It returns HTML because the dev toolbar is only injected into ``text/html``
responses — this is where you watch the footer come back on every click.

Every number on the page is read live from the router at render time. Nothing
is hardcoded, so if you add or delete a model the page keeps telling the
truth.
"""

from tina4_python.core.router import Router, get


def _counts() -> dict:
    """Read the raw router table — the exact thing the dev footer counts."""
    routes = Router.get_routes()
    crud, app, framework = [], [], []
    for r in routes:
        module = r["handler"].__module__ if r.get("handler") else "?"
        entry = f'{r["method"]} {r["path"]}'
        if module.startswith("tina4_python.crud"):
            crud.append(entry)
        elif module.startswith("tina4_python"):
            framework.append(entry)
        else:
            app.append(entry)
    return {"raw": len(routes), "crud": crud, "app": app, "framework": framework}


_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>debug-false repro &mdash; {heading}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0;
            margin: 0; padding: 3rem 1.5rem 7rem; line-height: 1.65; }}
    main {{ max-width: 48rem; margin: 0 auto; }}
    h1 {{ font-size: 1.55rem; margin: 0 0 0.2rem; }}
    h2 {{ font-size: 1.05rem; margin: 2.2rem 0 0.6rem; color: #93c5fd; }}
    p.sub {{ color: #94a3b8; margin: 0 0 1.5rem; }}
    ol {{ padding-left: 1.3rem; margin: 0; }}
    li {{ margin-bottom: 0.7rem; }}
    a {{ color: #60a5fa; }}
    code {{ background: #1e293b; padding: 0.1rem 0.35rem; border-radius: 0.25rem;
            font-size: 0.9em; }}
    .nav {{ margin-top: 2rem; display: flex; gap: 0.75rem; flex-wrap: wrap; }}
    .nav a {{ background: #1e293b; border: 1px solid #334155; padding: 0.5rem 1rem;
              border-radius: 0.5rem; text-decoration: none; }}
    table {{ border-collapse: collapse; margin-top: 0.5rem; font-size: 0.92rem; }}
    th, td {{ text-align: left; padding: 0.35rem 1.1rem 0.35rem 0; }}
    th {{ color: #94a3b8; font-weight: 500; border-bottom: 1px solid #334155; }}
    td.n {{ font-variant-numeric: tabular-nums; }}
    .big {{ font-size: 1.25rem; font-weight: 700; }}
    .warn {{ color: #fca5a5; }}
    .ok {{ color: #86efac; }}
  </style>
</head>
<body>
<main>
  <h1>{heading}</h1>
  <p class="sub">Mock app for the <code>TINA4_DEBUG=false</code> / dev-footer / route-count report.
     Everything below is measured live from this running server.</p>

  <h2>Claim B &mdash; the footer comes back on every click</h2>
  <ol>
    <li>Look at the dark bar pinned to the bottom of this page. Click its
        <code>&times;</code> to dismiss it, then click <em>page two</em> below.
        The footer is back. There is no environment flag that turns it off &mdash;
        only <code>TINA4_DEBUG=false</code>, which also kills the error overlay,
        live reload, <code>/__dev</code> and Swagger.</li>
    <li><strong>The tell:</strong> open the footer's <em>Dashboard &#8599;</em>
        link, then reload the page. The dashboard overlay <em>stays open</em> &mdash;
        it persists its state in <code>localStorage</code> under
        <code>tina4_dev_overlay_open</code>. The <code>&times;</code> sitting a few
        pixels away does not persist anything. Same bar, two different behaviours.</li>
  </ol>

  <h2>Claim C &mdash; the route count</h2>
  <p>The footer counts the <em>raw</em> router table. The <code>/__dev</code> dashboard
     counts a <em>filtered</em> view of the same table. They disagree:</p>

  <table>
    <tr><th>Source</th><th>What it counts</th><th>Number</th></tr>
    <tr><td>dev footer (bottom of this page)</td>
        <td><code>len(Router.get_routes())</code>, unfiltered</td>
        <td class="n big">{raw}</td></tr>
    <tr><td><code>/__dev/api/routes</code></td>
        <td>same table, internal prefixes removed</td>
        <td class="n big" id="apicount">fetching&hellip;</td></tr>
  </table>

  <p id="verdict" class="sub">&nbsp;</p>

  <p>The gap is <code>GET /health</code>. The framework registers <em>two</em> health
     routes &mdash; the canonical <code>/__health</code> plus a <code>/health</code>
     back-compat alias. The dashboard filters on the prefix tuple
     <code>("/__dev", "/health", "/swagger")</code>, and
     <code>"/__health".startswith("/health")</code> is <strong>False</strong>. So the
     alias is hidden, the canonical one is listed as though it were one of your own
     routes, and the two counts differ by one on every run. The same prefix would
     silently swallow an app route called <code>/healthz</code>.</p>

  <h2>Claim C &mdash; where {raw} comes from</h2>
  <p>Nothing here is padded. The breakdown of this app's router table:</p>
  <table>
    <tr><th>Origin</th><th>Count</th><th>Why</th></tr>
    <tr><td>AutoCRUD generated</td><td class="n">{n_crud}</td>
        <td>19 models in <code>src/orm/models.py</code> &times; 5 REST routes each</td></tr>
    <tr><td>hand-written</td><td class="n">{n_app}</td>
        <td>this file &mdash; one route, <code>/hello/{{page}}</code></td></tr>
    <tr><td>framework</td><td class="n">{n_fw}</td>
        <td>{fw_list}</td></tr>
    <tr><td><strong>raw total</strong></td><td class="n"><strong>{raw}</strong></td>
        <td>what the footer shows</td></tr>
  </table>
  <p>Delete a model from <code>src/orm/models.py</code>, restart, and the count drops
     by exactly 5. The number is honest &mdash; the footer just never says what it
     counts, and a project with 20 CRUD models has no way to learn that 100 of its
     routes were generated rather than written.</p>

  <div class="nav">
    <a href="/hello/one">page one</a>
    <a href="/hello/two">page two</a>
    <a href="/__dev/api/routes">/__dev/api/routes</a>
    <a href="/__dev">/__dev dashboard</a>
  </div>
</main>
<script>
fetch('/__dev/api/routes').then(function (r) {{ return r.json(); }}).then(function (d) {{
  var raw = {raw};
  document.getElementById('apicount').textContent = d.count;
  var v = document.getElementById('verdict');
  if (d.count === raw) {{
    v.innerHTML = '<span class="ok">The two counts agree on this run.</span>';
  }} else {{
    v.innerHTML = '<span class="warn">Mismatch: footer says ' + raw +
      ', dashboard says ' + d.count + ' &mdash; a difference of ' +
      (raw - d.count) + '. Both describe the same router table.</span>';
  }}
}}).catch(function () {{
  document.getElementById('apicount').textContent = 'unreachable (TINA4_DEBUG off?)';
}});
</script>
</body>
</html>
"""


@get("/hello/{page}")
async def hello(page, request, response):
    c = _counts()
    return response.html(_PAGE.format(
        heading=f"Click-me {page}",
        raw=c["raw"],
        n_crud=len(c["crud"]),
        n_app=len(c["app"]),
        n_fw=len(c["framework"]),
        fw_list=", ".join(f"<code>{e}</code>" for e in sorted(c["framework"])),
    ))
