# tutorial

Working notes for developing the Tina4 **tutorial / course** section. Nothing here ships. Edits
land in `tina4-book/book-7-course/` (chapters, which feed the PDF) and `tina4-documentation`
(a site section and its nav, neither of which exists yet).

## What already exists — read this before proposing anything

`book-7-course` is real, and further along than it looks. It is also **entirely unbuilt below the
syllabus**, and **published nowhere**.

| Path | Lines | State |
|---|--:|---|
| `book-7-course/chapters/01-how-this-course-works.md` | 109 | Written. Levels, the six-part module template, grading, the examiner, prerequisites |
| `book-7-course/chapters/02-syllabus.md` | 398 | Written. All **36 modules** named and described, three levels of twelve |
| `book-7-course/chapters/03..38` | — | **Do not exist.** Every module is a promise the syllabus makes and nothing keeps |
| `book-7-course/plan/BUGS-FOUND.md` | 227 | Five framework bugs found while grounding module 17, already filed upstream. See *Issues* below |
| `book-7-course/plan/UNDER-FIRE.md` | 258 | Audit of where Tina4's opinions are contestable, with a `SOURCE`/`DOCS` verification key |
| `tina4-documentation/docs/course/` | — | **Does not exist.** No section, no nav entry, nothing on tina4.com |

So the work is not "design a tutorial". The design is done and it is opinionated. The work is
**building 36 modules against a fixed template, and getting the section onto the site.**

### The structure to build against

Three levels of twelve modules, on Kent Beck's instruction with the last term changed —
*make it work, make it right, make it last*, because "fast is a property, lasting is a
discipline."

- **Level 1: Make It Work** — starts from never having written a line of code; ends able to build a
  small web application and explain every line.
- **Level 2: Make It Right** — ends able to write code another person can maintain without
  phoning you.
- **Level 3: Make It Last** — ends able to make an architectural decision, write down why, and
  defend it to a room that disagrees.

Each level ends in a capstone the student builds and defends.

**Every module has the same six parts**, and this is the constraint that makes the work hard:

1. **The Idea** — the concept in plain language, before any code.
2. **Build It** — working Tina4 code the student types, runs, and breaks.
3. **The Principle** — the named industry practice underneath, *with the source it comes from*.
   Not "the Tina4 way".
4. **Elsewhere** — the same principle in Django, Rails, Laravel, Express or Spring.
5. **When Not To** — the counter-case where applying the practice makes the software worse.
6. **Check Yourself** — the graded part.

Parts 3, 4 and 5 are why this cannot be written quickly. Part 3 needs a real citation. Part 4 needs
each comparative framework to be described correctly, which is a research task per module. Part 5
needs a genuine counter-case, not a hedge.

## Issues found while grounding the course

`book-7-course/plan/BUGS-FOUND.md` carries **seven** cross-language framework issues from an `Auth`
audit read in source across all four implementations. Five are filed upstream:

| Issue | Filed |
|---|---|
| JWT header advertises an algorithm the signature does not use | tina4-python#105 |
| `TINA4_JWT_ALGORITHM` ignored by Python | tina4-python#106 |
| `nbf` validated in Ruby only | tina4-python#107, tina4-php#187, tina4-nodejs#39 |

Two are unfiled by decision: the `aud`/`iss` gap (consistent across all four, so a design gap
rather than a defect) and the `get_payload` naming hazard (breaking, so a v4 discussion).

**None of these are in [`known-issues/ledger.md`](../known-issues/ledger.md)**, which claims to be
the single home for issues in this repo. They live in the *book* repo, so the 2026-08-13
consolidation did not reach them — that sweep covered this repo's root. They are ledger-shaped:
framework code, multiple languages, upstream filings, and Ruby named as the implementation that
gets `nbf` right. Migrating them is a decision, not an oversight.

## Working convention

`getstar/` did this job for the Getting Started section and was deleted on 2026-08-13 once the work
shipped as PRs. Two lessons, applied here from the start:

1. **A plan document outlives its decision and then lies.** `getstar/python-refinement.md` spent
   weeks as the authority on a page structure that was rejected, and needed a WITHDRAWN banner
   pasted on top. Date every decision here, and when one is reversed, say so at the top of the file
   rather than deep in a section.
2. **The record of what shipped belongs in the PR, not in the notes.** The PR description is
   permanent, reviewable, and outside this repo. Notes are scaffolding — expect this whole
   directory to be deleted once the modules land.

And the rule that governs all documentation work here: **the page states intended behaviour.** A
framework fault found while writing a module goes to
[`known-issues/ledger.md`](../known-issues/ledger.md), never onto the page. The course's own
`UNDER-FIRE.md` is the sanctioned exception in spirit — it discusses *contestable opinions*, which
is not the same as documenting defects.

## Mechanics worth knowing before the first edit

- `tina4-book/book-N-*/chapters/NN-*.md` is the only source for numbered chapters.
  `tina4-documentation/scripts/sync-books.sh` runs **book to docs** and deletes
  `docs/<section>/[0-9]*.md` before re-copying, so a chapter edit made on the docs side is
  destroyed on the next sync. Edit the book, then sync.
- `book.yml` per book drives `scripts/build_pdf.py`, which globs `chapters/NN-*.md`. Only numbered
  chapters reach the PDF.
- The docs site runs a strict CI gate, `scripts/audit-truth.py`: ASCII-only punctuation (no em
  dashes, smart quotes or ellipsis characters anywhere), and every `TINA4_*` name must resolve to a
  `getenv()` in one of the four framework source trees. A CLI-only variable fails it — that is
  ledger row `SITE-DOC-01`.
- Verify by running, not by reading. The Getting Started audit found **15 of 36** sections factually
  wrong, nine of which would not run at all, on a page that had been reviewed for years.

## Open questions

Nothing here is decided. These change what the work *is*, so they are worth answering before any
module is drafted.

1. **Is this repo authoring the course, or testing it?** `testing-tina4` is a QA harness — its
   protocol forbids authoring and requires every test to trace to a quoted documented claim.
   `getstar/` broke that boundary deliberately and shipped documentation. Same again, or does the
   course get written elsewhere and audited here?
2. **Which language do the modules teach in?** The syllabus is language-neutral and *Elsewhere*
   compares to Django, Rails, Laravel, Express and Spring, but *Build It* needs one concrete
   framework. Python, matching the rest of the work, or all four?
3. **Where does it publish?** Book-only (PDF), or a `docs/course/` site section with nav — which
   needs a `tina4press` group and does not exist today.
4. **How many modules, in what order?** 36 at six parts each is a large body of work. Level 1 alone
   is twelve modules and is the one with a real audience: someone who has never written code.
