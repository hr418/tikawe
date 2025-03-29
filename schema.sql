CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password_hash TEXT,
    UNIQUE (username COLLATE NOCASE)
);
