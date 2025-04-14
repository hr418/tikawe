CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password_hash TEXT,
    UNIQUE (username COLLATE NOCASE)
);

CREATE TABLE Events (
    id INTEGER PRIMARY KEY,
    user INTEGER REFERENCES Users,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    start INTEGER NOT NULL,
    end INTEGER NOT NULL,
    spots INTEGER,
    registeredCount INTEGER NOT NULL,
    isCanceled BOOLEAN NOT NULL
);

CREATE TABLE EventParticipants (
    id INTEGER PRIMARY KEY,
    event INTEGER REFERENCES Events ON DELETE CASCADE,
    user INTEGER REFERENCES Users,
    UNIQUE (event, user)
);

CREATE TABLE Tags (
    id INTEGER PRIMARY KEY,
    title TEXT,
    value TEXT
);

CREATE TABLE EventTags (
    id INTEGER PRIMARY KEY,
    event INTEGER REFERENCES Events ON DELETE CASCADE,
    title TEXT,
    value TEXT
);
