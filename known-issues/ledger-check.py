#!/usr/bin/env python3
"""Check known-issues/ledger.md, and optionally sort it and refresh its counts.

    python3 known-issues/ledger-check.py            # check only; exit 1 on any error
    python3 known-issues/ledger-check.py --write    # check, sort rows by Status then newest first, refresh counts

Errors (refuse to write): a row lost or duplicated against the last commit, a row with the
wrong number of cells, a Status outside the vocabulary or without a date, port keys out of
order. Warnings (reported, never block): a Status the port tokens contradict.

Columns are resolved by header name, never by position.
"""
import collections
import io
import os
import re
import subprocess
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ledger.md')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT = re.compile(r'(?<!\\)\|')
KEYS = ['py', 'php', 'rb', 'nd', 'js', 'dlp', 'cli']
ORDER = ['Investigating', 'Discussing', 'Fixing', 'Verifying', 'Backporting', 'Queued',
         'Blocked', 'Ready', 'Filed', 'Found', 'Merged', 'Closed', 'Dropped']
STATUS = re.compile(r'^(%s) (\d{4}-\d{2}-\d{2})$' % '|'.join(ORDER))
BEGIN, END = '<!-- counts:begin -->', '<!-- counts:end -->'


def cells(line):
    return [c.strip() for c in SPLIT.split(line)[1:-1]]


def table(lines):
    """Return (header index, header cells, [row line indices]) for the ledger table."""
    h = next(i for i, l in enumerate(lines) if l.startswith('| Code | Kind |'))
    head = cells(lines[h])
    rows = []
    i = h + 2
    while i < len(lines) and lines[i].startswith('|'):
        rows.append(i)
        i += 1
    return h, head, rows


def tokens(cell):
    out = collections.OrderedDict()
    for t in cell.split():
        k, _, v = t.partition(':')
        out[k] = v
    return out


def stage(v):
    return v.split('#')[0]


def codes_at(ref):
    try:
        text = subprocess.run(['git', '-C', REPO, 'show', '%s:known-issues/ledger.md' % ref],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return row_codes(text.split('\n'))


def row_codes(lines):
    """Codes of every row under any `| Code | Kind |` header — the old file had several tables."""
    out, intab = [], False
    for l in lines:
        if l.startswith('| Code | Kind |'):
            intab = True
            continue
        if not l.startswith('|'):
            intab = False
        elif intab and l.startswith('| `'):
            out.append(cells(l)[0])
    return out


def check(lines):
    errors, warnings = [], []
    h, head, rows = table(lines)
    col = {n: head.index(n) for n in head}
    for need in ('Code', 'Status', 'Port status', 'Doc verified'):
        if need not in col:
            errors.append('header has no %r column' % need)
            return errors, warnings, h, head, rows
    for i in rows:
        c = cells(lines[i])
        if len(c) != len(head):
            errors.append('line %d: %d cells, header has %d' % (i + 1, len(c), len(head)))
            continue
        code, st = c[col['Code']], c[col['Status']]
        m = STATUS.match(st)
        if not m:
            errors.append('%s: Status %r is not "<word> YYYY-MM-DD" from %s' % (code, st, ORDER))
            continue
        ps, dv = tokens(c[col['Port status']]), tokens(c[col['Doc verified']])
        for name, t in (('Port status', ps), ('Doc verified', dv)):
            if list(t) != KEYS:
                errors.append('%s: %s keys %s, want %s' % (code, name, list(t), KEYS))
        s = m.group(1)
        p = {stage(v) for v in ps.values()}
        d = {stage(v) for v in dv.values()}
        if s == 'Filed' and 'filed' not in p and 'filed' not in d:
            warnings.append('%s: Filed, but no port or doc token is filed#N' % code)
        if s == 'Ready' and 'fixed' not in p:
            warnings.append('%s: Ready, but no port is fixed' % code)
        if s in ('Merged', 'Closed') and p & {'affected', 'fixed', 'filed'}:
            warnings.append('%s: %s, but a port is still %s' % (code, s, sorted(p & {'affected', 'fixed', 'filed'})))
        if s == 'Closed' and ('?' in p or d & {'?', 'stale', 'filed'}):
            warnings.append('%s: Closed, but a check or a doc change is still owed' % code)
        if s == 'Found' and p & {'fixed', 'filed'}:
            warnings.append('%s: Found, but a port is already %s' % (code, sorted(p & {'fixed', 'filed'})))
    here = [cells(lines[i])[0] for i in rows]
    dupes = sorted(c for c, n in collections.Counter(here).items() if n > 1)
    if dupes:
        errors.append('duplicated rows: %s' % dupes)
    before = codes_at('HEAD')
    if before is not None:
        missing = sorted(set(before) - set(here))
        if missing:
            errors.append('rows lost since HEAD: %s' % missing)
    return errors, warnings, h, head, rows


def counts(lines, head, rows):
    col = {n: head.index(n) for n in head}
    n = collections.Counter(cells(lines[i])[col['Status']].split()[0] for i in rows)
    parts = ['%d %s' % (n[s], s) for s in ORDER if n[s]]
    return '%s\n**%d rows** by Status, computed by `ledger-check.py`: %s.\n%s' % (
        BEGIN, len(rows), ', '.join(parts), END)


def main():
    write = '--write' in sys.argv[1:]
    lines = io.open(PATH, encoding='utf-8').read().split('\n')
    errors, warnings, h, head, rows = check(lines)
    for w in warnings:
        print('warn:', w)
    for e in errors:
        print('ERROR:', e)
    if errors:
        print('%d error(s); nothing written.' % len(errors))
        return 1
    col = head.index('Status')
    if write:
        body = [lines[i] for i in rows]
        body.sort(key=lambda l: cells(l)[col].split()[1], reverse=True)  # newest first...
        body.sort(key=lambda l: ORDER.index(cells(l)[col].split()[0]))  # ...within each Status
        lines[rows[0]:rows[-1] + 1] = body
        text = '\n'.join(lines)
        block = counts(lines, head, rows)
        if BEGIN in text:
            text = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda _: block, text, flags=re.S)
        io.open(PATH, 'w', encoding='utf-8').write(text)
        e2, _, _, _, _ = check(text.split('\n'))
        if e2:
            print('ERROR after write:', e2)
            return 1
        print('written: %d rows sorted by Status, counts refreshed.' % len(rows))
    else:
        print('ok: %d rows, %d warning(s).' % (len(rows), len(warnings)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
