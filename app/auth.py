from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .db import get_db
from .security import verify_password, ALLOWED_ROLES

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        user = get_db().execute(
            "SELECT * FROM users WHERE username=? AND active=1",
            (username,)
        ).fetchone()

        if user and user["role"] in ALLOWED_ROLES and verify_password(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["full_name"]
            return redirect(url_for("web.dashboard"))

        flash("Incorrect username or password.", "error")

    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
