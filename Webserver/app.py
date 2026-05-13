# https://www.geeksforgeeks.org/python/how-to-use-flask-session-in-python-flask/
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from functools import wraps

app = Flask(__name__)

app.secret_key = "change_this_secret_key"

API_BASE_URL = "http://127.0.0.1:5000/api"


def is_logged_in():
    return session.get("logged_in") is True


def is_admin():
    return session.get("role_name") == "Admin"


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


@app.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            response = requests.post(
                f"{API_BASE_URL}/users/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                session["logged_in"] = True
                session["user_id"] = data.get("user_id")
                session["email"] = data.get("email")
                session["role_name"] = data.get("role_name")

                return redirect(url_for("dashboard"))

            elif response.status_code == 401:
                flash("Forkert adgangskode")

            elif response.status_code == 404:
                flash("Brugeren blev ikke fundet")

            else:
                flash("Der skete en fejl ved login")

        except requests.exceptions.RequestException:
            flash("Kunne ikke forbinde til API-serveren")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if not is_admin():
        return render_template("not_admin.html")

    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)