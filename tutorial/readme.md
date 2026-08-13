# tutorial

Working notes for developing the Tina4 **tutorial / course** section. Nothing here ships. Edits
land in `tina4-book/book-7-course/` (chapters, which feed the PDF) and `tina4-documentation`
(a site section and nav, neither of which exists yet).

## What already exists

The design is done. The modules are not.

| | |
|---|---|
| `book-7-course/chapters/01-how-this-course-works.md` | Written. Three levels, the six-part module template, grading |
| `book-7-course/chapters/02-syllabus.md` | Written. All **36 modules** named, twelve per level |
| Chapters 03 to 38 | **Do not exist** |
| `tina4-documentation/docs/course/` | **Does not exist.** Nothing on tina4.com |

Levels run *make it work · make it right · make it last*. Every module has the same six parts:
The Idea, Build It, The Principle, Elsewhere, When Not To, Check Yourself.

## Conventions

- **The book is the source.** `sync-books.sh` runs book to docs and deletes
  `docs/<section>/[0-9]*.md` before re-copying, so a chapter edited on the docs side is destroyed
  on the next sync.
- **Verify by running, not reading.** The Getting Started audit found 15 of 36 sections wrong on a
  page that had been reviewed for years.
- **Pages state intended behaviour.** A framework fault found while writing goes to
  [`known-issues/ledger.md`](../known-issues/ledger.md), never onto the page.
- **Date decisions, and mark reversals at the top of the file.** `getstar/` spent weeks with a plan
  document that authoritatively described a rejected structure.
- **The PR is the permanent record.** These notes are scaffolding; expect the directory to be
  deleted once the modules land.
