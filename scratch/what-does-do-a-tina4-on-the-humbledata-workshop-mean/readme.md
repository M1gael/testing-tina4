# What does "do a tina4 on" the HumbleData workshop mean?

Asked 2026-10-14 (boss in Slack, conference sponsored by CoderLevelUp): "git clone
HumbleData/beginners-data-workshop - I want you to do a tina4 on this".

## The workshop (`src/`, clone of `edf1345`, 2026-06-08)
- A beginner's Python + data workshop for conferences, run in the browser (JupyterLite).
  Also available locally (uv or conda), and in 5 languages.
- 6 notebooks: Beginning with Python, First steps with Pandas, Matplotlib, Seaborn, More
  Python basics, More Pandas.
  - 123 exercises.
  - Each exercise has a commented-out `# !cat solutions/NN_MM.py` cell that reveals an answer.
- Real CSV datasets: penguins, iris, pokemon, food training.
- Dependencies: jupyterlab, pandas, numpy, matplotlib, seaborn.
- Licence: CC BY-SA 4.0. Adapting it means crediting Humble Data and releasing the result
  under the same licence.

## What Tina4 already has
tina4-documentation `course/` and `docs/course/` hold "Learn to Code the Tina4 Way" (added
2026-08-29):
- 36 modules over 3 levels, of which 2 are written (module 1 the cafe menu, module 2 the
  receipt).
- Graded by `tina4grade.py`, which runs the code through the real TestClient and then has an
  LLM examiner mark comprehension answers. That needs a `TINA4_MCP_TOKEN`.
- It is a course, not a drop-in conference workshop: no browser runtime, no reveal-a-solution
  flow, no datasets.

## Readings
1. **Most likely:** build a Tina4 equivalent of this workshop: the same beginner,
   conference-ready shape (zero install or one `uv` command, exercise then reveal, real
   data), teaching Python by building with tina4-python.
2. Take the same datasets and do the data work the Tina4 way: load a CSV into the ORM or
   SQLite, serve it as an API, chart it in a Frond template.
3. Unlikely: audit or grind the repo itself.

## Answer (2026-10-14)
The user chose to borrow the shape only, with our own content under MPL. The plan is in
`gitdir/tina4-beginners-workshop/PLAN.md`, and the work goes section by section.

Runtime facts, run on py `074fa2eb`:
- Local Jupyter: everything works.
- JupyterLite: the TestClient fails (`f-rt-08`), a SQLite file on `/drive` fails (a JupyterLite limitation), and `!cat` / `%load` reveals don't work.

`make-reveal-notebook.py` is the reveal probe.

**Moved 2026-10-14:** the workshop repo, the builders (`build/`) and a copy of their repo now live
in the shell `gitdir/tina4-workshop/`. Start from its `HANDOVER.md`.
