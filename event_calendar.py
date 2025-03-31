from datetime import datetime
from flask import session
import db

def get_events():
    sql = """SELECT e.id, e.title, e.description, e.start, e.end, e.spots, e.registeredCount, e.isCanceled, u.username
             FROM Events e, Users u
             WHERE e.start >= ? AND e.user = u.id
             ORDER BY e.start"""
    return db.query(sql, [int(datetime.now().timestamp())])

def add_event(title, description, start, end, spots):
    user_id_sql = """SELECT u.id
             FROM Users u
             WHERE u.username = ?"""
    user_id = db.query(user_id_sql, [session["username"]])[0][0]

    sql = "INSERT INTO Events (user, title, description, start, end, spots, registeredCount, isCanceled) VALUES (?, ?, ?, ?, ?, ?, 0, 0)"
    db.execute(sql, [user_id, title, description, start, end, spots])

def edit_event(event_id, title, description, start, end, spots):
    sql = "UPDATE Events SET title = ? AND description = ? AND start = ? AND end = ? AND spots = ? WHERE id = ?"
    db.execute(sql, [title, description, start, end, spots, event_id])
 
def delete_event(event_id):
    sql = "DELETE FROM Events WHERE id = ?"
    db.execute(sql, [event_id])
