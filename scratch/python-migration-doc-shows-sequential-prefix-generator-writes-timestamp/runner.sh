#!/usr/bin/env bash
# Does the python runner accept and order hand-written 000001_ names (the kept "Sequential" table row)?
# 000002 inserts into the table 000001 creates, so a wrong order fails loudly.
set -u
W=${W:-$HOME/.cache/tina4-worktrees/verify-1029/d-orm-02}; T=$W/venv/bin/tina4python
app=$(mktemp -d); home=$(mktemp -d); cd "$app"; mkdir migrations data
# written in reverse so creation/glob order cannot be what orders them
echo "INSERT INTO notes (title) VALUES ('seeded');" > migrations/000002_seed_notes.sql
echo "CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL);" > migrations/000001_create_notes.sql
echo "DROP TABLE IF EXISTS notes;" > migrations/000001_create_notes.down.sql
echo "DELETE FROM notes;" > migrations/000002_seed_notes.down.sql
export HOME=$home TINA4_DATABASE_URL=sqlite:///data/app.db
echo "== migrate"; $T migrate 2>&1 | grep -E "Migrated|executed|rror"
echo "== rows"; $W/venv/bin/python -c "import sqlite3;print(sqlite3.connect('data/app.db').execute('select title from notes').fetchall())"
echo "== rollback"; $T migrate:rollback 2>&1 | grep -Ei "roll|rror"
echo "== tables after rollback"; $W/venv/bin/python -c "import sqlite3;print([r[0] for r in sqlite3.connect('data/app.db').execute(\"select name from sqlite_master where type='table' and name='notes'\")])"
cd /; rm -rf "$app" "$home"
