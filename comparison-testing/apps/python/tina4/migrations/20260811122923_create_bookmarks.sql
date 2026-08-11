CREATE TABLE bookmark
(
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url   TEXT NOT NULL
);

INSERT INTO bookmark (title, url) VALUES ('Tina4', 'https://tina4.com');
