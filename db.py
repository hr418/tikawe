import sqlite3
from flask import g


def get_connection():
    con = getattr(g, "database", None)
    if not con:
        con = g.database = sqlite3.connect("database.db")
        con.execute("PRAGMA foreign_keys = ON")
        con.row_factory = sqlite3.Row
    return con


def execute(sql, params=[]):
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid


def last_insert_id():
    return g.last_insert_id


def query(sql, params=[]):
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    return result


def close_connection():
    con = getattr(g, "database", None)
    if con:
        con.close()
