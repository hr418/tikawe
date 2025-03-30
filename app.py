import sqlite3
import re
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import config
import db
import event_calendar

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route("/")
def index():
    return render_template("index.html", events=event_calendar.get_events())

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Salasanat eivät täsmää.", redirect="/register")
    password_hash = generate_password_hash(password1)

    # Check if username contains more than one consequtive space, space as the first character, space as the last character, or illegal characters
    if re.search(r"\s{2,}|^ | $", username) or not re.fullmatch(r"[\w ]+", username):
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tunnus ei kelpaa.", redirect="/register")

    if len(password1) < 8:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Salasana ei ole tarpeeksi pitkä.", redirect="/register")

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tunnus on jo olemassa.", redirect="/register")

    return render_template("message.html", title="Onnistui", redirect_text="Etusivulle", message="Käyttäjä luotu.", redirect="/")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT password_hash FROM users WHERE username = ?"
    
    result = db.query(sql, [username])

    if not result:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Väärä tunnus tai salasana.", redirect="/")

    if check_password_hash(result[0][0], password):
        session["username"] = username
        return redirect("/")

    return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Väärä tunnus tai salasana.", redirect="/")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")
