# usage: scan.py <file.md>...  -> one line per un-awaited call to an async tina4-nodejs ORM/DB API
# Scope: fenced ts/typescript/js/javascript/untagged blocks only. A call counts as awaited when the
# expression it heads is preceded by `await`, `return` or `yield`, or is followed by `.then(`.
# APIs (all `async` on tina4-nodejs v3, packages/orm/src/database.ts + baseModel.ts + queryBuilder.ts):
#   Database.getConnection/create/fromEnv, initDatabase(), Model statics create/find/findById/
#   findOrFail/all/where/select/selectOne/count/exists/createTable/withTrashed/cached/eagerLoad,
#   instance hasMany/belongsTo/hasOne/save/load/forceDelete/restore, db.fetch/fetchOne/execute/
#   executeMany/insert/update/delete/truncate/startTransaction/commit/rollback/tableExists/
#   getTables/getColumns/getNextId, and query()...get()/first()/count()/exists() chains.
import re, sys

LANGS = {"", "ts", "typescript", "js", "javascript", "tsx", "mjs"}
NOT_MODELS = {"Object", "Array", "Promise", "JSON", "Math", "Date", "Router", "Number", "String",
              "Reflect", "Map", "Set", "Buffer", "Symbol", "Error", "Intl", "URL", "Response",
              "Request", "Queue", "Session", "Cache", "Auth", "Log", "Container", "Events"}
STATIC = r"create|find|findById|findOrFail|all|where|select|selectOne|count|exists|createTable|withTrashed|cached|eagerLoad"
PATS = [
    re.compile(r"\bDatabase\.(?:getConnection|create|fromEnv)\("),
    re.compile(r"(?<![\w.])initDatabase\("),
    re.compile(r"\b([A-Z]\w*)\.(?:" + STATIC + r")\("),
    re.compile(r"\.(?:hasMany|belongsTo|hasOne|forceDelete|restore)\("),
    re.compile(r"\b\w+\.(?:save|load|delete)\(\)"),
    re.compile(r"\b(?:db|database|conn|tx)\.(?:fetch|fetchOne|fetchAll|execute|executeMany|insert|update|delete|truncate|startTransaction|commit|rollback|tableExists|getTables|getColumns|getNextId)\("),
    re.compile(r"\.query\(\)"),  # QueryBuilder chain: only counted if it ends in get/first/count/exists
    re.compile(r"\bQueryBuilder\.fromTable\("),  # same rule
    re.compile(r"\bqb\.(?:get|first|count|exists)\(\)"),
    re.compile(r"\bqb\s*\n?\s*\.\w+\("),  # multi-line qb chain, same rule as .query()
]
CHAINED = {r"\.query\(\)", r"\bQueryBuilder\.fromTable\(", r"\bqb\s*\n?\s*\.\w+\("}

def blocks(text):
    out, cur, lang, inb, start = [], [], None, False, 0
    for n, l in enumerate(text.split("\n"), 1):
        m = re.match(r"^\s*```\s*([\w+-]*)", l)
        if m:
            if inb:
                if lang in LANGS: out.append((start, cur))
                cur, inb = [], False
            else:
                lang, inb, start = m.group(1).lower(), True, n + 1
            continue
        if inb: cur.append(l)
    return out

def expr_start(src, i):
    """walk back from i over a member/call chain (crossing newlines before a leading dot)"""
    j = i
    while j > 0:
        c = src[j - 1]
        if c.isalnum() or c in "_$.":
            j -= 1
        elif c == ")":
            d, k = 0, j - 1
            while k >= 0:
                if src[k] == ")": d += 1
                elif src[k] == "(":
                    d -= 1
                    if d == 0: break
                k -= 1
            j = k
        elif c in " \t\n":
            k = j
            while k > 0 and src[k - 1] in " \t\n": k -= 1
            # continue across whitespace only if the chain continues with a dot
            if src[j:].lstrip().startswith(".") and src[k - 1:k] not in ("", ";", "{", "}", "(", ",", "=") :
                j = k
            else:
                break
        else:
            break
    return j

def call_end(src, i):
    k = src.index("(", i); d = 0
    while k < len(src):
        if src[k] == "(": d += 1
        elif src[k] == ")":
            d -= 1
            if d == 0: return k + 1
        k += 1
    return len(src)

def chain_end(src, e):
    """extend past further .x(...) calls, including across newlines"""
    while True:
        m = re.match(r"\s*\.\w+\(", src[e:])
        if not m: return e
        e = call_end(src, e + m.end() - 1)

def scan(path):
    text = open(path).read(); hits = []
    # user scopes: statics that return this.where()/all()/... and names registered with Model.scope()
    scopes = set(re.findall(r"static\s+(\w+)\([^)]*\)\s*\{\s*return\s+this\.(?:" + STATIC + r")\(", text))
    scopes |= set(re.findall(r"\.scope\(\s*\"(\w+)\"", text))
    pats = PATS + ([re.compile(r"\.(?:" + "|".join(sorted(scopes)) + r")\(")] if scopes else [])
    for start, lines in blocks(text):
        src = "\n".join(lines)
        # skip comment-only text
        for pat in pats:
            for m in pat.finditer(src):
                if pat.groups and (m.group(1) in NOT_MODELS or m.group(1).isupper()): continue
                if re.match(r"\bsession\.", m.group(0)): continue  # Session.save() is sync
                ls = src.rfind("\n", 0, m.start()) + 1
                line = src[ls:src.find("\n", m.start()) if src.find("\n", m.start()) >= 0 else len(src)]
                if line.lstrip().startswith(("//", "*", "#")) or "//" in src[ls:m.start()]: continue
                if re.search(r"\b(async|static)\s+$", src[ls:m.start()]) or re.match(r"\s*(static\s+)?(async\s+)?\w+\(.*\)\s*[:{]", line) and "." not in line.split("(")[0]:
                    continue  # a definition, not a call
                s = expr_start(src, m.start() + 1 if src[m.start()] == "." else m.start())
                e = chain_end(src, call_end(src, m.start()))
                chain = src[s:e]
                if pat.pattern in CHAINED and not re.search(r"\.(get|first|count|exists)\(\s*\)\s*$", chain):
                    continue
                before = src[:s].rstrip()
                if re.search(r"(\bawait|\byield)$", before): continue
                # `return X()` hands the promise to an awaiting caller only if X() is the whole value
                if re.search(r"\breturn$", before) and re.match(r"\s*(;|\)|\}|$)", src[e:]): continue
                if re.match(r"\s*\.then\(", src[e:]): continue
                if ".then(" in chain[chain.find(m.group(0)) :]: continue
                ln = start + src[:m.start()].count("\n")
                hits.append((ln, line.strip()))
    heads = [(n, l.lstrip("#").strip()) for n, l in enumerate(text.split("\n"), 1) if re.match(r"#{1,4} ", l)]
    seen = set()
    for ln, l in sorted(hits):
        if (ln, l) in seen: continue
        h = next((t for n, t in reversed(heads) if n < ln), "")
        seen.add((ln, l)); print(f"{path}:{ln}: [{h}] {l}")

for p in sys.argv[1:]: scan(p)
