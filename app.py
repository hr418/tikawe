import sqlite3
import re
from functools import wraps
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import config
import db
import event_calendar

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Kirjaudu",
                    message="Et ole kirjautunut sisään.",
                    redirect="/login",
                ),
                401,
            )
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")

    return render_template(
        "index.html",
        events=list(
            map(event_calendar.format_event_display, event_calendar.get_events())
        ),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Kaikki kentät ovat pakollisia.",
                    redirect="/login",
                ),
                400,
            )

        sql = "SELECT password_hash FROM users WHERE username = ?"

        result = db.query(sql, [username])

        if not result:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Väärä tunnus tai salasana.",
                    redirect="/",
                ),
                401,
            )

        if check_password_hash(result[0][0], password):
            sql = "SELECT id FROM users WHERE username = ?"

            result = db.query(sql, [username])
            session["user_id"] = result[0][0]
            session["username"] = username
            return redirect("/")

        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Väärä tunnus tai salasana.",
                redirect="/",
            ),
            401,
        )


@app.route("/logout")
@require_login
def logout():
    del session["user_id"]
    del session["username"]
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if not username or not password1 or not password2:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Kaikki kentät ovat pakollisia.",
                    redirect="/register",
                ),
                400,
            )

        if password1 != password2:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Salasanat eivät täsmää.",
                    redirect="/register",
                ),
                400,
            )

        if len(password1) < 8:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Salasana ei ole tarpeeksi pitkä.",
                    redirect="/register",
                ),
                400,
            )
        if len(password1) > 30:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Salasana ei voi olla pidempi kuin 30 merkkiä.",
                    redirect="/register",
                ),
                400,
            )
        if len(username) > 30:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Tunnus ei voi olla pidempi kuin 30 merkkiä.",
                    redirect="/register",
                ),
                400,
            )
        # Check if username contains more than one consequtive space, space as the first character, space as the last character, or illegal characters
        if re.search(r"\s{2,}|^ | $", username) or not re.fullmatch(
            r"[\w ]+", username
        ):
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Tunnus ei kelpaa.",
                    redirect="/register",
                ),
                400,
            )

        password_hash = generate_password_hash(password1)

        try:
            sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
            db.execute(sql, [username, password_hash])
        except sqlite3.IntegrityError:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Tunnus on jo olemassa.",
                    redirect="/register",
                ),
                409,
            )

        return render_template(
            "message.html",
            title="Onnistui",
            redirect_text="Etusivulle",
            message="Käyttäjä luotu.",
            redirect="/",
        )


@app.route("/new_event", methods=["GET", "POST"])
@require_login
def new_event():
    tags = event_calendar.get_tags()

    if request.method == "GET":
        return render_template("new_event.html", tags=tags)

    if request.method == "POST":
        form = event_calendar.event_form_handler(request.form, tags)

        if form["error"]:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message=form["error"],
                    redirect="/new_event",
                ),
                400,
            )

        try:
            event_calendar.add_event(
                form["title"],
                form["description"],
                form["start_epoch"],
                form["end_epoch"],
                form["spots"],
                form["tags"],
            )
        except sqlite3.Error:

            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Tuntemattomasta syystä, tapahtumaa ei voitu lisätä tietokantaan.",
                    redirect="/new_event",
                ),
                500,
            )
        return render_template(
            "message.html",
            title="Onnistui",
            redirect_text="Etusivulle",
            message="Tapahtuma luotu.",
            redirect="/",
        )


@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
@require_login
def edit_event(event_id):
    event = event_calendar.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )
    if event["user"] != session["user_id"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Sinulla ei ole oikeuksia muokata tätä tapahtumaa.",
                redirect="/",
            ),
            403,
        )
    tags = event_calendar.get_tags()

    if request.method == "GET":
        event_tags = event_calendar.get_event_tags(event_id)

        return render_template(
            "edit_event.html",
            event=event_calendar.format_event_form(event),
            tags=tags,
            event_tags=event_tags,
        )

    if request.method == "POST":
        form = event_calendar.event_form_handler(request.form, tags)

        if form["error"]:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message=form["error"],
                    redirect="/new_event",
                ),
                400,
            )

        try:
            event_calendar.edit_event(
                event_id,
                form["title"],
                form["description"],
                form["start_epoch"],
                form["end_epoch"],
                form["spots"],
                form["tags"],
            )
        except sqlite3.Error:
            return (
                render_template(
                    "message.html",
                    title="Virhe",
                    redirect_text="Takaisin",
                    message="Tuntemattomasta syystä, tapahtumaa ei voitu päivittää tietokantaan.",
                    redirect=f"/edit/{event_id}",
                ),
                500,
            )

        return render_template(
            "message.html",
            title="Onnistui",
            redirect_text="Etusivulle",
            message="Tapahtuma päivitetty.",
            redirect="/",
        )


@app.route("/delete/<int:event_id>", methods=["GET", "POST"])
@require_login
def delete(event_id):
    event = event_calendar.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )
    if event["user"] != session["user_id"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Sinulla ei ole oikeuksia poistaa tätä tapahtumaa.",
                redirect="/",
            ),
            403,
        )
    if request.method == "GET":
        return render_template("delete_event.html", event_id=event_id)

    if request.method == "POST":
        if "continue" in request.form:
            try:
                event_calendar.delete_event(event_id)
            except sqlite3.Error:
                return (
                    render_template(
                        "message.html",
                        title="Virhe",
                        redirect_text="Takaisin",
                        message="Tuntemattomasta syystä, tapahtumaa ei voitu poistaa.",
                        redirect=f"/event/{event_id}",
                    ),
                    500,
                )
            return render_template(
                "message.html",
                title="Onnistui",
                redirect_text="Etusivulle",
                message="Viesti poistettu.",
                redirect="/",
            )
        return redirect("/")
