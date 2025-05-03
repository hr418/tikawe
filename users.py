from datetime import datetime
import math
import db


def get_user(user_id):
    sql = """SELECT u.id, u.username, u.createdAt
             FROM Users u
             WHERE u.id = ?"""
    result = db.query(sql, [user_id])
    user = result[0] if result else None

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
