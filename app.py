import sqlite3
import re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
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

        sql = "SELECT passwordHash FROM users WHERE username = ?"

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
            r"^[a-öA-Ö0-9_]+$", username
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
            sql = (
                "INSERT INTO users (username, passwordHash, createdAt) VALUES (?, ?, ?)"
            )
            db.execute(sql, [username, password_hash, int(datetime.now().timestamp())])
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
    available_tags = tags.get_tags()

    if request.method == "GET":
        return render_template("new_event.html", tags=available_tags)

    if request.method == "POST":
        form = events.event_form_handler(request.form, available_tags)

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
            events.add_event(
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


@app.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@require_login
def edit_event(event_id):
    event = events.get_event(event_id)

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
    if event["username"] != session["username"]:
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
    available_tags = tags.get_tags()

    if request.method == "GET":
        event_tags = tags.get_event_tags(event_id)

        return render_template(
            "edit_event.html",
            event=events.format_event_form(event),
            tags=available_tags,
            event_tags=event_tags,
        )

    if request.method == "POST":
        form = events.event_form_handler(request.form, available_tags)

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


@app.route("/event/<int:event_id>/delete", methods=["GET", "POST"])
@require_login
def delete(event_id):
    event = events.get_event(event_id)

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
    if event["username"] != session["username"]:
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
                events.delete_event(event_id)
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


@app.route("/event/<int:event_id>")
@require_login
def event(event_id):
    event = events.get_event(event_id)

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
    return render_template(
        "event.html",
        event=events.format_event_display(event),
        tags=tags.format_tags_display(tags.get_event_tags(event_id)),
        is_participant=events.is_event_participant(event_id, session["user_id"]),
        participants=events.get_event_participants(event_id),
    )


@app.route("/event/<int:event_id>/register", methods=["POST", "GET"])
@require_login
def register_to_event(event_id):
    event = events.get_event(event_id)

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

    if event["isCanceled"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Tapahtuma on peruttu.",
                redirect=f"/event/{event_id}",
            ),
            400,
        )

    if event["spots"] and event["registeredCount"] >= event["spots"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Tapahtuma on täynnä.",
                redirect=f"/event/{event_id}",
            ),
            400,
        )

    if events.is_event_participant(event_id, session["user_id"]):
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Olet jo ilmoittautunut tapahtumaan.",
                redirect=f"/event/{event_id}",
            ),
            400,
        )
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
                return (
                    render_template(
                        "message.html",
                        title="Virhe",
                        redirect_text="Takaisin",
                        message="Tuntemattomasta syystä, ilmoittautuminen ei onnistunut.",
                        redirect=f"/event/{event_id}",
                    ),
                    500,
                )
            return render_template(
                "message.html",
                title="Onnistui",
                redirect_text="Etusivulle",
                message="Ilmoittautuminen onnistui.",
                redirect="/",
            )
        if "cancel" in request.form:
            return redirect(f"/event/{event_id}")


@app.route("/event/<int:event_id>/unregister", methods=["POST", "GET"])
@require_login
def unregister_from_event(event_id):
    event = events.get_event(event_id)

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

    if not events.is_event_participant(event_id, session["user_id"]):
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
                message="Et ole rekisteröitynyt tapahtumaan.",
                redirect=f"/event/{event_id}",
            ),
            400,
        )

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
                return (
                    render_template(
                        "message.html",
                        title="Virhe",
                        redirect_text="Takaisin",
                        message="Tuntemattomasta syystä, peruminen ei onnistunut.",
                        redirect=f"/event/{event_id}",
                    ),
                    500,
                )
            return render_template(
                "message.html",
                title="Onnistui",
                redirect_text="Etusivulle",
                message="Ilmoittautumisesi on peruttu.",
                redirect="/",
            )
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
                redirect_text="Takaisin",
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
def cancel_event(event_id):
    event = events.get_event(event_id)

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

    if event["username"] != session["username"]:
        return (
            render_template(
                "message.html",
                title="Virhe",
                redirect_text="Takaisin",
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
                return (
                    render_template(
                        "message.html",
                        title="Virhe",
                        redirect_text="Takaisin",
                        message="Tuntemattomasta syystä, tapahtumaa ei voitu perua.",
                        redirect=f"/event/{event_id}",
                    ),
                    500,
                )
            return render_template(
                "message.html",
                title="Onnistui",
                redirect_text="Etusivulle",
                message="Tapahtuma peruttu.",
                redirect="/",
            )
        if "cancel" in request.form:
            return redirect(f"/event/{event_id}")
