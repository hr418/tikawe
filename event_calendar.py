from datetime import datetime
from flask import session
import db


def get_events():
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username
             FROM Events e, Users u
             WHERE e.start >= ? AND e.user = u.id
             ORDER BY e.start"""
    return db.query(sql, [int(datetime.now().timestamp())])


def get_event(event_id):
    sql = """SELECT *
             FROM Events e
             WHERE e.id =?"""
    return db.query(sql, [event_id])[0] if db.query(sql, [event_id]) else None


def add_event(title, description, start, end, spots):
    user_id = session["user_id"]

    sql = "INSERT INTO Events (user, title, description, start, end, spots, registeredCount, isCanceled) VALUES (?, ?, ?, ?, ?, ?, 0, 0)"
    db.execute(sql, [user_id, title, description, start, end, spots])


def edit_event(event_id, title, description, start, end, spots):
    sql = "UPDATE Events SET title = ?, description = ?, start = ?, end = ?, spots = ? WHERE id = ?"
    db.execute(sql, [title, description, start, end, spots, event_id])


def delete_event(event_id):
    sql = "DELETE FROM Events WHERE id = ?"
    db.execute(sql, [event_id])


# Formats event attributes for display
def format_event_display(event):
    start = datetime.fromtimestamp(event["start"])
    end = datetime.fromtimestamp(event["end"])

    result = {}
    result["id"] = event["id"]
    result["title"] = event["title"]
    result["description"] = event["description"]
    result["username"] = event["username"]
    result["is_canceled"] = event["isCanceled"]
    result["spots"] = (
        f"{event["registeredCount"]} / {event["spots"]} ilmoittautunut"
        if event["spots"]
        else f"{event["registeredCount"]} ilmoittautunut"
    )
    result["date"] = f"{start.day}.{start.month}"
    result["duration"] = (
        f"{start.strftime("%d/%m/%Y %H:%M")} - {end.strftime("%d/%m/%Y %H:%M")}"
    )

    return result


# Formats event attributes to be used as values in html form
def format_event_form(event):
    start = datetime.fromtimestamp(event["start"])
    end = datetime.fromtimestamp(event["end"])

    result = {}
    result["id"] = event["id"]
    result["title"] = event["title"]
    result["description"] = event["description"]
    result["spots"] = event["spots"]
    result["start_date"] = start.strftime("%Y-%m-%d")
    result["start_time"] = start.strftime("%H:%M")
    result["end_date"] = end.strftime("%Y-%m-%d")
    result["end_time"] = end.strftime("%H:%M")

    return result


# Validates event form data
def event_form_handler(form):
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

    return {
        "title": title,
        "description": description,
        "start_epoch": start_epoch,
        "end_epoch": end_epoch,
        "spots": None if not spots else int(spots),
        "error": None,
    }
