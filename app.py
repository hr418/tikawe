import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, session, redirect, flash
import config
import db
import events
import users
import tags

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


def check_csrf_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            csrf_token = request.form.get("csrf_token")
            if csrf_token != session.get("csrf_token"):
                return (
                    render_template(
                        "message.html",
                        title="Virhe",
                        redirect_text="Etusivulle",
                        message="CSRF esto.",
                        redirect="/",
                    ),
                    403,
                )
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")

    return render_template(
        "index.html",
        events=list(map(events.format_event_display, events.get_events())),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", filled={})
    if request.method == "POST":
        user = users.login_form_handler(request.form)

        if user["error"]:
            flash("!" + user["error"])
            return render_template("login.html", filled=user["filled"])

        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["csrf_token"] = user["csrf_token"]

        return redirect("/")


@app.route("/logout")
@require_login
@check_csrf_token
def logout():
    del session["user_id"]
    del session["username"]
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})
    if request.method == "POST":
        user = users.register_form_handler(request.form)

        if user["error"]:
            flash("!" + user["error"])
            return render_template("register.html", filled=user["filled"])

        try:
            sql = (
                "INSERT INTO users (username, passwordHash, createdAt) VALUES (?, ?, ?)"
            )
            db.execute(
                sql,
                [
                    user["username"],
                    user["password_hash"],
                    int(datetime.now().timestamp()),
                ],
            )
        except sqlite3.Error as e:
            if "UNIQUE constraint failed" in str(e):
                flash("!Tunnus on jo olemassa.")
                return render_template("register.html", filled=user["filled"])
            flash("!Tuntemattomasta syystä, käyttäjää ei voitu luoda.")
            return render_template("register.html", filled=user["filled"])

        flash("Käyttäjä luotu. Voit nyt kirjautua sisään.")
        return redirect("/login")


@app.route("/new_event", methods=["GET", "POST"])
@require_login
@check_csrf_token
def new_event():
    available_tags = tags.get_tags()

    if request.method == "GET":
        return render_template(
            "new_event.html", tags=available_tags, filled={"tags": {}}
        )

    if request.method == "POST":
        form = events.event_form_handler(request.form, available_tags)

        if form["error"]:
            flash("!" + form["error"])
            return render_template(
                "new_event.html", tags=available_tags, filled=form["filled"]
            )

        try:
            event_id = events.add_event(
                form["title"],
                form["description"],
                form["start_epoch"],
                form["end_epoch"],
                form["spots"],
                form["tags"],
            )
        except sqlite3.Error:
            flash("!Tuntemattomasta syystä, tapahtumaa ei voitu lisätä tietokantaan.")
            return render_template(
                "new_event.html", tags=available_tags, filled=form["filled"]
            )

        flash("Tapahtuma luotu.")
        return redirect(f"/event/{event_id}")


@app.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@require_login
@check_csrf_token
def edit_event(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )
    if event["username"] != session["username"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Sinulla ei ole oikeuksia muokata tätä tapahtumaa.",
                redirect="/",
            ),
            403,
        )
    available_tags = tags.get_tags()

    if request.method == "GET":
        filled = events.format_event_form(event)
        filled["tags"] = tags.get_event_tags(event_id)

        return render_template(
            "edit_event.html",
            filled=filled,
            tags=available_tags,
            event_id=event_id,
        )

    if request.method == "POST":
        form = events.event_form_handler(request.form, available_tags)

        if form["error"]:
            flash("!" + form["error"])
            return render_template(
                "edit_event.html",
                tags=available_tags,
                filled=form["filled"],
                event_id=event_id,
            )

        try:
            events.edit_event(
                event_id,
                form["title"],
                form["description"],
                form["start_epoch"],
                form["end_epoch"],
                form["spots"],
                form["tags"],
            )
        except sqlite3.Error:
            flash(
                "!Tuntemattomasta syystä, tapahtumaa ei voitu päivittää tietokantaan."
            )
            return render_template(
                "edit_event.html",
                tags=available_tags,
                filled=form["filled"],
                event_id=event_id,
            )

        flash("Tapahtuma päivitetty.")
        return redirect(f"/event/{event_id}")


@app.route("/event/<int:event_id>/delete", methods=["GET", "POST"])
@require_login
@check_csrf_token
def delete(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )
    if event["username"] != session["username"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
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
                events.delete_event(event_id)
            except sqlite3.Error:
                flash("!Tuntemattomasta syystä, tapahtumaa ei voitu poistaa.")
                redirect(f"/event/{event_id}")
            flash("Tapahtuma poistettu.")
            return redirect("/")
        return redirect("/")


@app.route("/event/<int:event_id>")
@require_login
def event(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )
    return render_template(
        "event.html",
        event=events.format_event_display(event),
        tags=tags.format_tags_display(tags.get_event_tags(event_id)),
        is_participant=events.is_event_participant(event_id, session["user_id"]),
        participants=events.get_event_participants(event_id),
    )


@app.route("/event/<int:event_id>/register", methods=["POST", "GET"])
@require_login
@check_csrf_token
def register_to_event(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )

    if event["isCanceled"]:
        flash("!Tapahtuma on peruttu.")
        return redirect(f"/event/{event_id}")

    if event["spots"] and event["registeredCount"] >= event["spots"]:
        flash("!Tapahtuma on täynnä.")
        return redirect(f"/event/{event_id}")

    if events.is_event_participant(event_id, session["user_id"]):
        flash("!Olet jo ilmoittautunut tapahtumaan.")
        return redirect(f"/event/{event_id}")

    if request.method == "GET":
        return render_template(
            "register_to_event.html",
            event=events.format_event_display(event),
        )

    if request.method == "POST":
        if "continue" in request.form:
            try:
                events.register_to_event(event_id, session["user_id"])
            except sqlite3.Error:
                flash("!Tuntemattomasta syystä, ilmoittautuminen ei onnistunut.")
                return redirect(f"/event/{event_id}")

            flash("Ilmoittautuminen onnistui.")
            return redirect(f"/event/{event_id}")
        if "cancel" in request.form:
            return redirect(f"/event/{event_id}")


@app.route("/event/<int:event_id>/unregister", methods=["POST", "GET"])
@require_login
@check_csrf_token
def unregister_from_event(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )

    if not events.is_event_participant(event_id, session["user_id"]):
        flash("!Et ole ilmoittautunut tapahtumaan.")
        return redirect(f"/event/{event_id}")

    if request.method == "GET":
        return render_template(
            "unregister_from_event.html",
            event=events.format_event_display(event),
        )

    if request.method == "POST":
        if "continue" in request.form:
            try:
                events.unregister_from_event(event_id, session["user_id"])
            except sqlite3.Error:
                flash(
                    "!Tuntemattomasta syystä, ilmoittautumisen peruminen ei onnistunut."
                )
                return redirect(f"/event/{event_id}")

            flash("Ilmoittautuminen peruttu.")
            return redirect(f"/event/{event_id}")
        if "cancel" in request.form:
            return redirect(f"/event/{event_id}")


@app.route("/user/<int:user_id>")
@require_login
def user(user_id):
    user = users.get_user(user_id)

    if not user:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Käyttäjää ei löydy.",
                redirect="/",
            ),
            404,
        )

    return render_template(
        "user.html",
        user=user,
        events=list(
            map(
                events.format_event_display,
                events.get_user_events(user_id),
            )
        ),
        participations=list(
            map(
                events.format_event_display,
                events.get_user_participations(user_id),
            )
        ),
    )


@app.route("/event/<int:event_id>/cancel", methods=["POST", "GET"])
@require_login
@check_csrf_token
def cancel_event(event_id):
    event = events.get_event(event_id)

    if not event:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Tapahtuma on poistettu tai sitä ei ole olemassa.",
                redirect="/",
            ),
            404,
        )

    if event["username"] != session["username"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Etusivulle",
                message="Sinulla ei ole oikeutta perua tätä tapahtumaa.",
                redirect="/",
            ),
            403,
        )

    if request.method == "GET":
        return render_template(
            "cancel_event.html",
            event=events.format_event_display(event),
        )

    if request.method == "POST":
        if "continue" in request.form:
            try:
                events.cancel_event(event_id)
            except sqlite3.Error:
                flash("!Tuntemattomasta syystä, tapahtumaa ei voitu perua.")
                return redirect(f"/event/{event_id}")

            flash("Tapahtuma peruttu.")
            return redirect(f"/event/{event_id}")
        if "cancel" in request.form:
            return redirect(f"/event/{event_id}")
