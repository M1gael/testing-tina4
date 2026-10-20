# A typed ORM model silently drops undeclared columns on save (php 3.13.138+)

Question: why does airoffices `tests/CompanyLoginServiceTest.php` fail on tina4php 3.13.150/3.13.151 but pass on 3.13.132 and 3.13.97?

Answer: from 3.13.138, a model that declares any public property writes only its declared properties. `Company` declares 11 but not `loginUsername`, `loginPassword`, `isActive` or `isDeleted`. The test's seed sets those dynamically, `save()` drops them without a word and returns the model, so the row commits with `login_username` NULL and every login lookup misses. It is not a commit bug.

Trees: airoffices `staging` `58909b0b` (clone `~/gitdir/airoffices`, never committed to or pushed). tina4-php `origin/v3` `77156098` (tip, 13 commits past 3.13.151) and tags. All runs were in a throwaway worktree with a copy of the staging snapshot DB and `HOME` redirected.

## Runs

| tina4php | CompanyLoginServiceTest | `ZzProbeTest` typed model, undeclared `code` | `find()` returns |
|---|---|---|---|
| 3.13.97 (staging pin) | 7/7 | - | array |
| 3.13.132 | 7/7 | written | ModelCollection |
| 3.13.137 | 7/7 | written | ModelCollection |
| 3.13.138 | 3 fail | **NULL** | ModelCollection |
| 3.13.150 | 3 fail | NULL | ModelCollection |
| 3.13.151 | 3 fail | NULL | ModelCollection |
| tip `77156098` | 3 fail | NULL | ModelCollection |

`find()` return type and the closed-schema code by version were read from the tags.

- `ZzCompanyProbeTest` on 3.13.151 and tip: `save=model id=3 row_by_id={"login_username":null,"is_active":1} row_by_login=null`. The row commits, but the login column is NULL. `is_active=1` is the DB default, not the assigned value.
- The 3 failures are exactly the 3 tests that need a successful login. The 4 that pass expect a failed login, so they pass whatever the cause: the inactive-company seed also loses `isActive=0`.
- Both directions, on tip: declaring those 4 properties on `src/orm/Company.php` gives 7/7; reverting gives 3 failures again.

## Mechanism (tip, `vendor/tina4stack/tina4php/Tina4/ORM.php`; read, then run)

- `:2498` `declaredColumnDefinitions()`: the subclass's public properties become the whole column set.
- `:1596` `resolveFieldColumn()`: with that set non-empty, it returns null for any other name, including a real column (`login_username`).
- `:3000-3013` `getDbData()`: "ADR-0069 G2: only the model's own fields reach the column list"; `if (!$isField) continue;`. No log, no error.
- `:555-563` `__set()`: its comment still says an undeclared dynamic set counts as a caller assignment.
- Introduced by `2996be4e` "ORM save() writes only the model's fields" (2026-09-24). Its commit message says it applies to INSERT and UPDATE, and to values from `fill()` as well as assignment. First release containing it: 3.13.138.

## Reach in airoffices

Read: 9 of 54 ORM models declare public properties, so their column set closes on 3.13.138+: Address, Company, Document, Location, Partner, QrCode, ReviewFormConfig, ScanLog, SecurityCodes.

Run: an instrumented full suite on tip logged every dropped non-null write to a real column. Logging only, then removed:
- Company: `isActive` and `isDeleted` 28 times each, `loginUsername` and `loginPassword` 6 times each.
- Location: `thumbnailImg` and `bannerImg`, 3 each.
- Address: `isDeleted`, 2.

Those are the paths the suite covers. App code also writes these names elsewhere (read), e.g. `HostDashboardService.php:1594` `loginPassword`, `LocationManagementService.php:793-794`. Where the model is one of the 9 and the property is undeclared, the write is lost.

## The coworker's report against this

| Claim | Verdict |
|---|---|
| `getNextId`/`tina4_sequences` id collision | No. The ORM never calls it, and the app has no `getNextId` or `tina4_sequences` reference (read). |
| `save()` reports ok, row never persists; ORM commit wrapper broken | No. The row persists (`row_by_id`). The value is dropped before the INSERT, so a lookup by username finds nothing. |
| Raw INSERT persists, ORM `save()` does not | Consistent with the above: the raw INSERT names `login_username` explicitly (inferred; their SQL not seen). |
| `TINA4_AUTOCOMMIT` does not help | Expected: transactions are not involved. |
| 3.13.132 clean, 3.13.150 broken | Yes. The exact boundary is 3.13.137 ok, 3.13.138 broken (run). |
| ModelCollection migration needed from 3.13.132 | Yes (read). `find()` returns `ModelCollection` from 3.13.132. On tip, 233 suite tests fail with `array_map`/`usort` TypeErrors. That is loud, separate, and what the 68-file migration addresses. Their migration is in no pushed branch, so it was not seen. |

## Options (not decided)

App-side:
1. Declare every column the app writes on the 9 closed models. Verified for Company: 7/7 on tip.
2. Pin 3.13.137: it has the ModelCollection `find()` and no closed schema (run: 7/7, probe writes). It loses later fixes.
3. Stop declaring properties on those models so their columns are introspected. This loses the typed properties; not tested.

Framework-side:
1. Keep ADR-0069 G2 but fail loud when a dropped property names a real column (log or throw).
2. Let a dynamic property that resolves to a real column through.
3. Document the rule in the upgrade notes.
Also fix the `__set` comment either way.

## Bounds

- php only. Other ports not checked.
- ADR-0069 text not found in any local repo; intent read from the commit message only.
- Drops measured only on paths the suite exercises.
- The DB is an April staging snapshot. The coworker's DB (company ids 1-82) was not seen.
- Our full-suite baseline on 3.13.97 is already red (275 failing; no `.env`), so suite counts are relative only.
- Not checked: UPDATE paths at runtime (the commit message says UPDATE is covered); production configuration.

## Fix attempt (grindfix, 2026-10-19, tina4-php `77156098`)

`repro.php <tina4-php tree> <work dir>` — framework-only, SQLite. Stock: cases A (assign),
C (change after load), F (fill) all `save=ok` with the value lost.

Candidate in `~/.cache/tina4-worktrees/orm28-php` (uncommitted): `save()` refuses, before any
transaction, when an undeclared property names a real column and differs from what was read
from the database (every read path records it via `markHydrated()`). After: A/C/F
`save=false` with the reason; load-then-save, join extras and untyped models unchanged.
New `tests/OrmUndeclaredColumnAssignmentTest.php`: 17 tests, 5 fail on stock.

Blocker: upstream deliberately locks the silent drop in. `IdentifierAllowListContractTest::
testOrmSaveWritesOnlyDeclaredFields` (and its python/ruby/nodejs twins, python is master)
asserts that `save()` succeeds while dropping an undeclared real column, on insert and update.
It is the only test the candidate turns red. Refusing needs that contract changed in all four
ports — a maintainer decision.

### Revised: warn, don't refuse

The refusal is superseded. `fix.patch` keeps G2 as is (the value is still not written) and
has `save()` log a `WARNING` naming the property and column, once per model class and property
per process. After: case A logs `Typed::save() did not write 'loginUsername' to column
'login_username': ... Declare $loginUsername on the model to write it.` Full suite failure set is
identical to stock; the G2 contract test stays green. The new test has 17 tests, and 5 fail on stock.

### Revised again: no column lookup

The column check cost one metadata query per model class per connection, so it is gone.
`save()` now warns about any undeclared property the caller set on a model that declares
fields, whether or not it names a column (G2 never writes it either way). Values read back
by a load, or as join extras, stay quiet. The new test has 18 tests, and 6 fail on stock.
The full suite's failure set is identical to stock.
