from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .model import User

bp = Blueprint("auth", __name__, template_folder="templates")

@bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/register.html")

@bp.post("/register")
def register_post():
    email = request.form.get("email", "").strip().lower()
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")

    # basic validation
    if not email or not name or not password:
        flash("All fields are required.")
        return redirect(url_for("auth.register"))

    # unique email
    if db.session.execute(db.select(User).where(User.email == email)).scalar():
        flash("Email already registered.")
        return redirect(url_for("auth.register"))

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Account created! You can now log in.")
    return redirect(url_for("auth.login"))

@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")

@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    if not user or not user.check_password(password):
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    login_user(user)
    return redirect(url_for("main.index"))

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
