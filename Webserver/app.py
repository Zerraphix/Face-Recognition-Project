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
                session["first_name"] = data.get("first_name")
                session["last_name"] = data.get("last_name")
                session["email"] = data.get("email")
                session["role_id"] = data.get("role_id")
                session["role_name"] = data.get("role_name")
                session["has_face_data"] = data.get("has_face_data", False)

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
    return render_template(
        "dashboard.html",
        is_admin=is_admin()
    )


@app.route("/upload-face", methods=["POST"])
@login_required
def upload_face():
    file = request.files.get("file")

    if file is None or file.filename == "":
        flash("Du skal vælge et billede")
        return redirect(url_for("dashboard"))

    try:
        files = {
            "file": (
                file.filename,
                file.stream,
                file.mimetype
            )
        }

        data = {
            "user_id": session["user_id"],
            "is_active": "true"
        }

        response = requests.post(
            f"{API_BASE_URL}/faces",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code == 201:
            session["has_face_data"] = True
            flash("Face data blev uploadet")
        else:
            flash(f"Upload fejlede: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)