import random
import sqlite3
from datetime import datetime

db = sqlite3.connect("database.db")
db.execute("PRAGMA foreign_keys = ON")
db.row_factory = sqlite3.Row


def get_tags():
    sql = """SELECT t.title, t.value
             FROM Tags t"""
    tags = db.execute(sql).fetchall()

    result = {}
    for tag in tags:
        if tag["title"] not in result:
            result[tag["title"]] = []
        result[tag["title"]].append(tag["value"])
    return result


available_tags = get_tags()

db.close()

db = sqlite3.connect("database.db")

db.execute("DELETE FROM Users")
db.execute("DELETE FROM Events")
db.execute("DELETE FROM EventParticipants")
db.execute("DELETE FROM EventTags")


user_count = 1000
event_count = 10**5
participant_count = 10**6
now = int(datetime.now().timestamp())

for i in range(1, user_count + 1):
    db.execute(
        "INSERT INTO Users (username, createdAt) VALUES (?, ?)", ["user" + str(i), 0]
    )

for i in range(1, event_count + 1):
    db.execute(
        "INSERT INTO Events (user, title, description, start, end, spots, registeredCount, isCanceled) VALUES (?, ?, ?, ?, ?, ?, 0, 0)",
        [
            random.randint(1, user_count),
            "event" + str(i),
            "description" + str(i),
            random.randint(now, now + 86400),
            random.randint(now + 86400, now + (86400 * 2)),
            random.randint(1, 10000),
        ],
    )

    for tag, values in available_tags.items():
        if random.randint(0, 1):
            db.execute(
                "INSERT INTO EventTags (event, title, value) VALUES (?, ?, ?)",
                [i, tag, random.choice(values)],
            )

for i in range(1, participant_count + 1):
    try:
        db.execute(
            "INSERT INTO EventParticipants (event, user) VALUES (?, ?)",
            [random.randint(1, event_count), random.randint(1, user_count)],
        )
    except sqlite3.IntegrityError:
        continue

db.commit()
db.close()
