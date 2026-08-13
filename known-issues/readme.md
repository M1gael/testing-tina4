# known-issues

**Purpose not yet settled — see the warning below before putting anything here.**

## The record already has a Known Issues Log

`findings-log.md` → `## Known Issues Log` is the canonical home for confirmed findings, and
`CLAUDE.md` names it as such. It currently holds **67 rows** across roughly 670 of that file's
1135 lines, in the six-column schema `documentation-testing/readme.md` → *Issue Report Format*
defines.

So this directory must not become a second place where findings live. Two homes for one record
means drift, and the first symptom is a fixed issue that is still open in the other copy.

## Two workable jobs for this directory

Pick one deliberately, then delete the other from this file.

1. **Split the KI Log out of `findings-log.md`.** One markdown per issue (`PY-18-03.md`) or per
   chapter (`py-ch18.md`), with `findings-log.md` keeping only an index. Worth doing if the log
   has outgrown the single file — at 670 lines it arguably has. Requires updating `CLAUDE.md`,
   `documentation-testing/readme.md`, and every inbound link.
2. **Long-form write-ups per issue, index staying put.** The KI Log rows stay in
   `findings-log.md` as the one-line record; this directory carries the evidence that will not
   fit a table cell. That is close to what `bug-hunting/` already does for assigned `BH-<n>`
   investigations, so check that directory first rather than duplicating it.

## Until then

Empty on purpose. Nothing here is authoritative.
