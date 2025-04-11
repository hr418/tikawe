import sqlite3
import re
from datetime import datetime
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import config
import db
import event_calendar
import utils

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")

    return render_template("index.html", events=map(utils.event_formatter, event_calendar.get_events()))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
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

    if len(password1) < 8:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Salasana ei ole tarpeeksi pitkä.", redirect="/register")
    
    if len(password1) > 30:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Salasana ei voi olla pidempi kuin 30 merkkiä.", redirect="/register")
    
    if len(username) > 30:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tunnus ei voi olla pidempi kuin 30 merkkiä.", redirect="/register")

    # Check if username contains more than one consequtive space, space as the first character, space as the last character, or illegal characters
    if re.search(r"\s{2,}|^ | $", username) or not re.fullmatch(r"[\w ]+", username):
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tunnus ei kelpaa.", redirect="/register")

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tunnus on jo olemassa.", redirect="/register")

    return render_template("message.html", title="Onnistui", redirect_text="Etusivulle", message="Käyttäjä luotu.", redirect="/")

@app.route("/new_event", methods=["GET", "POST"])
def new_event():
    if request.method == "GET":
        return render_template("new_event.html")
    
    title = request.form["title"]
    description = request.form["description"]
    start_date = request.form["start_date"]
    start_time = request.form["start_time"]
    end_date = request.form["end_date"]
    end_time = request.form["end_time"]
    spots = request.form["spots"]

    if not title or not description or not start_date or not start_time or not end_date or not end_time:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Varmista että kaikki pakolliset kentät ovat täytetty.", redirect="/new_event")
    
    start = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").timestamp()
    end = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").timestamp()

    if start < datetime.now().timestamp():
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tapahtuma ei voi alkaa menneisyydessä.", redirect="/new_event")
    
    if end <= start:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tapahtuma ei voi luppua, sen jälkeen kun se on alkanut.", redirect="/new_event")
    
    spots = None if not spots else int(spots)

    try:
        event_calendar.add_event(title, description, start, end, spots)
    except sqlite3.Error:
        return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Jokin meni pieleen.", redirect="/new_event")
    
    return render_template("message.html", title="Onnistui", redirect_text="Etusivulle", message="Tapahtuma luotu.", redirect="/")
    
@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if request.method == "GET":
        return render_template("edit_event.html", event_id=event_id)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        start_time = request.form["start_time"]
        end_date = request.form["end_date"]
        end_time = request.form["end_time"]
        spots = request.form["spots"]

        if not title or not description or not start_date or not start_time or not end_date or not end_time:
            return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Varmista että kaikki pakolliset kentät ovat täytetty.", redirect=f"/edit/{event_id}")

        start = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").timestamp()
        end = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").timestamp()

        if start < datetime.now().timestamp():
            return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tapahtuma ei voi alkaa menneisyydessä.", redirect=f"/edit/{event_id}")

        if end <= start:
            return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Tapahtuma ei voi luppua, sen jälkeen kun se on alkanut.", redirect=f"/edit/{event_id}")
        
        spots = None if not spots else int(spots)

        try:
            event_calendar.edit_event(event_id, title, description, start, end, spots)
        except sqlite3.Error:
            return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Jokin meni pieleen.", redirect=f"/edit/{event_id}")

        return render_template("message.html", title="Onnistui", redirect_text="Etusivulle", message="Tapahtuma muokattu.", redirect="/")

@app.route("/delete/<int:event_id>", methods=["GET", "POST"])
def delete(event_id):
    if request.method == "GET":
        return render_template("delete_event.html", event_id=event_id)

    if request.method == "POST":
        if "continue" in request.form:
            try:
                event_calendar.delete_event(event_id)
            except sqlite3.Error:
                return render_template("message.html", title="Virhe", redirect_text="Takaisin", message="Jokin meni pieleen.", redirect=f"/edit/{event_id}")
            return render_template("message.html", title="Onnistui", redirect_text="Etusivulle", message="Viesti poistettu.", redirect="/")
        return redirect("/")