from datetime import datetime

def event_formatter(event):
    start = datetime.fromtimestamp(event["start"])
    end = datetime.fromtimestamp(event["end"])

    result = {}
    result["id"] = event["id"]
    result["title"] = event["title"]
    result["description"] = event["description"]
    result["username"] = event["username"]
    result["is_canceled"] = event["isCanceled"]
    result["spots"] = f"{event["registeredCount"]} / {event["spots"]} ilmoittautunut" if event["spots"] else f"{event["registeredCount"]} ilmoittautunut"
    result["date"] = f"{start.day}.{start.month}"
    result["duration"] = f"{start.strftime("%d/%m/%Y %H:%M")} - {end.strftime("%d/%m/%Y %H:%M")}"

    return result

def event_form_handler(form):
    title = form["title"]
    description = form["description"]
    start_date = form["start_date"]
    start_time = form["start_time"]
    end_date = form["end_date"]
    end_time = form["end_time"]
    spots = form["spots"]

    if not title or not description or not start_date or not start_time or not end_date or not end_time:
        return {"error": "Varmista että kaikki pakolliset kentät ovat täytetty."}

    if len(title) > 50:
        return {"error": "Otsikko ei voi olla pidempi kuin 50 merkkiä."}
    
    if len(description) > 5000:
        return {"error": "Kuvaus ei voi olla pidempi kuin 5000 merkkiä."}

    start_epoch = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").timestamp()
    end_epoch = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").timestamp()

    if start_epoch < datetime.now().timestamp():
        return {"error": "Tapahtuma ei voi alkaa menneisyydessä."}

    if end_epoch < start_epoch:
        return {"error": "Tapahtuma ei voi loppua, sen jälkeen kun se on alkanut."}

    return {"title": title,
            "description": description,
            "start_epoch": start_epoch,
            "end_epoch": end_epoch,
            "spots": None if not spots else int(spots),
            "error": None
            }
