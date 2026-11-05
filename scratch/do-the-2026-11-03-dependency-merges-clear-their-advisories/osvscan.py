#!/usr/bin/env python3
"""Usage: osvscan.py <lockfile>  (uv.lock, composer.lock, package-lock.json)
Prints every locked package that OSV says is affected, one line each: name version scope ids.
Exit 2 if OSV is unreachable (never reported as clean)."""
import json, sys, tomllib, urllib.request, os
path = sys.argv[1]; base = os.path.basename(path)
pk = []  # (eco, name, version, scope)
if base == 'uv.lock':
    for p in tomllib.load(open(path, 'rb'))['package']:
        if 'version' in p and p.get('source', {}).get('registry'):
            pk.append(('PyPI', p['name'], p['version'], ''))
elif base == 'composer.lock':
    d = json.load(open(path))
    for scope in ('packages', 'packages-dev'):
        for p in d.get(scope) or []:
            pk.append(('Packagist', p['name'], p['version'].lstrip('v'), 'dev' if scope.endswith('dev') else 'prod'))
elif base == 'package-lock.json':
    for k, p in json.load(open(path))['packages'].items():
        if not k or p.get('link') or 'version' not in p: continue
        name = p.get('name') or k.split('node_modules/')[-1]
        pk.append(('npm', name, p['version'], 'dev' if p.get('dev') else 'prod'))
uniq = sorted(set(pk))
hits = []
for i in range(0, len(uniq), 500):
    chunk = uniq[i:i+500]
    q = {'queries': [{'package': {'ecosystem': e, 'name': n}, 'version': v} for e, n, v, _ in chunk]}
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request('https://api.osv.dev/v1/querybatch',
            data=json.dumps(q).encode(), headers={'Content-Type': 'application/json'}), timeout=60))
    except Exception as ex:
        print('ERROR OSV unreachable:', ex); sys.exit(2)
    for (e, n, v, s), res in zip(chunk, r['results']):
        ids = [x['id'] for x in res.get('vulns', [])]
        if ids: hits.append(f'{n} {v} {s} {" ".join(sorted(ids))}')
print(f'{len(uniq)} packages, {len(hits)} affected')
for h in hits: print(h)
