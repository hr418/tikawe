from datetime import datetime
import math
import re
import secrets
from werkzeug.security import check_password_hash, generate_password_hash
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
             WHERE e.user = ? AND e.start >= ? AND e.isCanceled = 0"""
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


def login_form_handler(form):
    username = form["username"]
    password = form["password"]

    filled = {"username": username, "password": password}

    if not username or not password:
        return {"error": "Kaikki kentät ovat pakollisia.", "filled": filled}

    sql = "SELECT passwordHash FROM users WHERE username = ?"
    result = db.query(sql, [username])

    if not result:
        return {"error": "Väärä tunnus tai salasana.", "filled": filled}

    if check_password_hash(result[0][0], password):
        sql = "SELECT id FROM users WHERE username = ?"

        result = db.query(sql, [username])
        return {
            "error": None,
            "user_id": result[0][0],
            "username": username,
            "csrf_token": secrets.token_hex(16),
            "filled": filled,
        }

    return {"error": "Väärä tunnus tai salasana.", "filled": filled}


def register_form_handler(form):
    username = form["username"]
    password1 = form["password1"]
    password2 = form["password2"]

    filled = {"username": username, "password1": password1, "password2": password2}

    if not username or not password1 or not password2:
        return {"error": "Kaikki kentät ovat pakollisia.", "filled": filled}

    if password1 != password2:
        return {"error": "Salasanat eivät täsmää.", "filled": filled}

    if len(password1) < 8:
        return {"error": "Salasana ei ole tarpeeksi pitkä.", "filled": filled}

    if len(password1) > 30:
        return {
            "error": "Salasana ei voi olla pidempi kuin 30 merkkiä.",
            "filled": filled,
        }

    if len(username) > 30:
        return {
            "error": "Tunnus ei voi olla pidempi kuin 30 merkkiä.",
            "filled": filled,
        }

    # Check if username contains more than one consequtive space, space as the first character, space as the last character, or illegal characters
    if re.search(r"\s{2,}|^ | $", username) or not re.fullmatch(
        r"^[a-öA-Ö0-9_]+$", username
    ):
        return {"error": "Tunnus ei kelpaa.", "filled": filled}

    return {
        "error": None,
        "username": username,
        "password_hash": generate_password_hash(password1),
        "filled": filled,
    }
