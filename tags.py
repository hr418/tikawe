import db


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


def format_tags_display(tags):
    result = []
    for tag, value in tags.items():
        result.append(f"{tag}: {value}")
    return result
