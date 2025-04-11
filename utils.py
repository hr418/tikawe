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