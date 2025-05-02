from datetime import datetime
import math
from flask import session
import db


def get_events():
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username, u.id AS user_id
             FROM Events e, Users u
             WHERE e.start >= ? AND e.user = u.id
             ORDER BY e.start"""
    return db.query(sql, [int(datetime.now().timestamp())])


def get_event(event_id):
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username, u.id AS user_id
             FROM Events e, users u
             WHERE e.id =? AND e.user = u.id"""
    return db.query(sql, [event_id])[0] if db.query(sql, [event_id]) else None


def get_event_participants(event_id):
    sql = """SELECT u.username, u.id
             FROM EventParticipants ep, Users u
             WHERE ep.event = ? AND ep.user = u.id"""
    return db.query(sql, [event_id]) if db.query(sql, [event_id]) else None


def get_user_events(user_id):
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username, u.id AS user_id
             FROM Events e, Users u
             WHERE e.user = ? AND e.start >= ? AND e.user = u.id
             ORDER BY e.start"""
    return db.query(sql, [user_id, int(datetime.now().timestamp())])


def get_user_participations(user_id):
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username, u.id AS user_id
             FROM EventParticipants ep, Events e, Users u
             WHERE ep.user = ? AND ep.event = e.id AND e.user = u.id AND e.start >= ?
             ORDER BY e.start"""
    return db.query(sql, [user_id, int(datetime.now().timestamp())])


def get_user(user_id):
    sql = """SELECT u.id, u.username, u.createdAt
             FROM Users u
             WHERE u.id = ?"""

    user = db.query(sql, [user_id])[0] if db.query(sql, [user_id]) else None

    if not user:
        return None

    sql = """SELECT COUNT(e.id) AS event_count, IFNULL(SUM(e.registeredCount), 0) AS total_participants
             FROM Events e
             WHERE e.user = ? AND e.start >= ?"""
    statistics = db.query(sql, [user_id, int(datetime.now().timestamp())])[0]

    account_age = math.floor(
        (datetime.now().timestamp() - user["createdAt"]) / 86400
    )  # seconds to days

    return {
        "id": user["id"],
        "username": user["username"],
        "event_count": statistics["event_count"],
        "total_participants": statistics["total_participants"],
        "account_age": account_age,
    }


def add_event(title, description, start, end, spots, tags):
    user_id = session["user_id"]

    sql = "INSERT INTO Events (user, title, description, start, end, spots, registeredCount, isCanceled) VALUES (?, ?, ?, ?, ?, ?, 0, 0)"
    db.execute(sql, [user_id, title, description, start, end, spots])
    event_id = db.last_insert_id()

    sql = "INSERT INTO EventTags (event, title, value) VALUES (?, ?, ?)"
    for tag, value in tags.items():
        db.execute(sql, [event_id, tag, value])


def edit_event(event_id, title, description, start, end, spots, tags):
    sql = "DELETE FROM EventTags WHERE event = ?"
    db.execute(sql, [event_id])
    for tag, value in tags.items():
        sql = "INSERT INTO EventTags (event, title, value) VALUES (?, ?, ?)"
        db.execute(sql, [event_id, tag, value])

    sql = "UPDATE Events SET title = ?, description = ?, start = ?, end = ?, spots = ? WHERE id = ?"
    db.execute(sql, [title, description, start, end, spots, event_id])


def cancel_event(event_id):
    sql = "UPDATE Events SET isCanceled = 1 WHERE id = ?"
    db.execute(sql, [event_id])

    sql = "DELETE FROM EventParticipants WHERE event = ?"
    db.execute(sql, [event_id])

    sql = "UPDATE Events SET registeredCount = 0 WHERE id = ?"
    db.execute(sql, [event_id])


def register_to_event(event_id, user_id):
    sql = "UPDATE Events SET registeredCount = registeredCount + 1 WHERE id = ?"
    db.execute(sql, [event_id])

    sql = "INSERT INTO EventParticipants (event, user) VALUES (?, ?)"
    db.execute(sql, [event_id, user_id])


def unregister_from_event(event_id, user_id):
    sql = "UPDATE Events SET registeredCount = registeredCount - 1 WHERE id = ?"
    db.execute(sql, [event_id])

    sql = "DELETE FROM EventParticipants WHERE event = ? AND user = ?"
    db.execute(sql, [event_id, user_id])


def is_event_participant(event_id, user_id):
    sql = "SELECT * FROM EventParticipants WHERE event = ? AND user = ?"
    result = db.query(sql, [event_id, user_id])
    return len(result) > 0


def delete_event(event_id):
    sql = "DELETE FROM Events WHERE id = ?"
    db.execute(sql, [event_id])


def get_tags():
    sql = """SELECT t.title, t.value
             FROM Tags t"""
    tags = db.query(sql)

    result = {}
    for tag in tags:
        if tag["title"] not in result:
            result[tag["title"]] = []
        result[tag["title"]].append(tag["value"])
    return result


def get_event_tags(event_id):
    sql = """SELECT t.title, t.value
             FROM EventTags t
             WHERE t.event = ?"""
    tags = db.query(sql, [event_id])

    result = {}
    for tag in tags:
        result[tag["title"]] = tag["value"]
    return result


# Formats event attributes for display
def format_event_display(event):
    start = datetime.fromtimestamp(event["start"])
    end = datetime.fromtimestamp(event["end"])

    result = {}
    result["id"] = event["id"]
    result["title"] = event["title"]
    result["description"] = event["description"]
    result["username"] = event["username"]
    result["user_id"] = event["user_id"]
    result["is_canceled"] = event["isCanceled"]
    result["spots"] = (
        f"{event["registeredCount"]} / {event["spots"]}"
        if event["spots"]
        else f"{event["registeredCount"]}"
    )
    result["date"] = f"{start.day}.{start.month}"
    result["duration"] = (
        f"{start.strftime("%d/%m/%Y %H:%M")} - {end.strftime("%d/%m/%Y %H:%M")}"
    )

    return result


def format_tags_display(tags):
    result = []
    for tag, value in tags.items():
        result.append(f"{tag}: {value}")
    return result


# Formats event attributes to be used as values in html form
def format_event_form(event):
    start = datetime.fromtimestamp(event["start"])
    end = datetime.fromtimestamp(event["end"])

    result = {}
    result["id"] = event["id"]
    result["title"] = event["title"]
    result["description"] = event["description"]
    result["spots"] = event["spots"] if event["spots"] else ""
    result["start_date"] = start.strftime("%Y-%m-%d")
    result["start_time"] = start.strftime("%H:%M")
    result["end_date"] = end.strftime("%Y-%m-%d")
    result["end_time"] = end.strftime("%H:%M")

    return result


# Validates event form data and formats for database
def event_form_handler(form, possible_tags):
    title = form["title"]
    description = form["description"]
    start_date = form["start_date"]
    start_time = form["start_time"]
    end_date = form["end_date"]
    end_time = form["end_time"]
    spots = form["spots"]

    if (
        not title
        or not description
        or not start_date
        or not start_time
        or not end_date
        or not end_time
    ):
        return {"error": "Varmista että kaikki pakolliset kentät ovat täytetty."}

    if len(title) > 50:
        return {"error": "Otsikko ei voi olla pidempi kuin 50 merkkiä."}

    if len(description) > 5000:
        return {"error": "Kuvaus ei voi olla pidempi kuin 5000 merkkiä."}

    if spots and not spots.isdigit():
        return {"error": "Paikkojen määrä on oltava numero."}

    if spots and int(spots) < 1:
        return {"error": "Paikkojen määrä on oltava suurempi kuin 0."}

    if spots and int(spots) > 9999999:
        return {"error": "Paikkojen määrä ei voi olla suurempi kuin 9999999."}

    start_epoch = datetime.strptime(
        f"{start_date} {start_time}", "%Y-%m-%d %H:%M"
    ).timestamp()
    end_epoch = datetime.strptime(
        f"{end_date} {end_time}", "%Y-%m-%d %H:%M"
    ).timestamp()

    if (
        start_epoch > datetime.now().timestamp() + 315569260
        or end_epoch > datetime.now().timestamp() + 315569260
    ):
        # 315569260 seconds = 10 years
        return {"error": "Tapahtuma ei voi alkaa tai loppua yli 10 vuoden päästä."}

    if start_epoch < datetime.now().timestamp():
        return {"error": "Tapahtuma ei voi alkaa menneisyydessä."}

    if end_epoch < start_epoch:
        return {"error": "Tapahtuma ei voi loppua, sen jälkeen kun se on alkanut."}

    event_tags = {}

    for tag in possible_tags:
        if tag not in form or form[tag] == "not_specified":
            continue
        tag_value = form[tag]
        if tag_value not in possible_tags[tag]:
            return {"error": f"Luokittelun {tag} arvo '{tag_value}' ei ole sallittu."}
        event_tags[tag] = tag_value

    return {
        "title": title,
        "description": description,
        "start_epoch": start_epoch,
        "end_epoch": end_epoch,
        "spots": None if not spots else int(spots),
        "tags": event_tags,
        "error": None,
    }
