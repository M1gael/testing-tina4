-- Migration: create_notes_table
-- Created: 2026-04-01 08:52:09

CREATE TABLE notes_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
