from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_restx import Api
import requests
from functools import wraps

from database.init_db import create_tables, seed_data
from api.role_api import api_role
from api.user_api import api_user
from api.log_api import api_log
from api.face_api import api_face
from api.pin_api import api_pin


app = Flask(__name__)

app.secret_key = "change_this_secret_key"

API_BASE_URL = "http://127.0.0.1:5000/api"


# API setup
api = Api(
    app,
    title="Face Access API",
    version="1.0",
    description="API til ansigtsgenkendelse og adgangskontrol",
    doc="/docs"
)

api.add_namespace(api_role, path="/api/roles")
api.add_namespace(api_user, path="/api/users")
api.add_namespace(api_log, path="/api/logs")
api.add_namespace(api_face, path="/api/faces")
api.add_namespace(api_pin, path="/api/pins")



# Login helpers
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


def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))

        if not is_admin():
            flash("Du har ikke adgang til admin-siden")
            return redirect(url_for("dashboard"))

        return route_function(*args, **kwargs)

    return wrapper

# Website routes
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
    face = None

    try:
        response = requests.get(
            f"{API_BASE_URL}/faces/user/{session['user_id']}",
            timeout=5
        )

        if response.status_code == 200:
            faces = response.json()

            if len(faces) > 0:
                face = faces[0]
        else:
            flash("Kunne ikke hente face data")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return render_template(
        "dashboard.html",
        is_admin=is_admin(),
        face=face
    )

@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

@app.route("/upload-face", methods=["POST"])
@login_required
def upload_face():
    file = request.files.get("file")
    face_id = request.form.get("face_id")

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
            "is_active": "true" if is_admin() else "false"
        }

        if face_id:
            response = requests.patch(
                f"{API_BASE_URL}/faces/{face_id}",
                data=data,
                files=files,
                timeout=10
            )
        else:
            response = requests.post(
                f"{API_BASE_URL}/faces",
                data=data,
                files=files,
                timeout=10
            )

        if response.status_code in [200, 201]:
            if is_admin():
                session["has_face_data"] = True
                flash("Face billede blev gemt og aktiveret")
            else:
                flash("Face billede blev gemt og afventer admin godkendelse")
        else:
            flash(f"Upload fejlede: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Admin user routes
@app.route("/admin/users")
@admin_required
def admin_users():
    users = []
    roles = []
    edit_user = None

    edit_user_id = request.args.get("edit_user_id")

    try:
        users_response = requests.get(
            f"{API_BASE_URL}/users",
            timeout=5
        )

        if users_response.status_code == 200:
            users = users_response.json()
        else:
            flash("Kunne ikke hente users fra API")

        roles_response = requests.get(
            f"{API_BASE_URL}/roles",
            timeout=5
        )

        if roles_response.status_code == 200:
            roles = roles_response.json()
        else:
            flash("Kunne ikke hente roller fra API")

        if edit_user_id:
            edit_response = requests.get(
                f"{API_BASE_URL}/users/{edit_user_id}",
                timeout=5
            )

            if edit_response.status_code == 200:
                edit_user = edit_response.json()
            else:
                flash("Kunne ikke hente user til redigering")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return render_template(
        "admin_users.html",
        users=users,
        roles=roles,
        edit_user=edit_user
    )


@app.route("/admin/users/create", methods=["POST"])
@admin_required
def admin_create_user():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")
    role_id = request.form.get("role_id")

    try:
        response = requests.post(
            f"{API_BASE_URL}/users",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password_hash": password,
                "role_id": int(role_id)
            },
            timeout=5
        )

        if response.status_code == 201:
            flash("User blev oprettet")
        else:
            flash(f"User kunne ikke oprettes: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_users"))


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if user_id == session.get("user_id"):
        flash("Du kan ikke slette dig selv mens du er logget ind")
        return redirect(url_for("admin_users"))

    try:
        response = requests.delete(
            f"{API_BASE_URL}/users/{user_id}",
            timeout=5
        )

        if response.status_code == 200:
            flash("User blev slettet")
        else:
            flash(f"User kunne ikke slettes: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_users"))

@app.route("/admin/users/update/<int:user_id>", methods=["POST"])
@admin_required
def admin_update_user(user_id):
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")
    role_id = request.form.get("role_id")

    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role_id": int(role_id)
        }

        if password is not None and password != "":
            data["password"] = password

        response = requests.put(
            f"{API_BASE_URL}/users/{user_id}",
            json=data,
            timeout=5
        )

        if response.status_code == 200:
            flash("User blev opdateret")
        else:
            flash(f"User kunne ikke opdateres: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_users"))

# Admin log routes
@app.route("/admin/logs")
@admin_required
def admin_logs():
    logs = []

    try:
        response = requests.get(
            f"{API_BASE_URL}/logs",
            timeout=5
        )

        if response.status_code == 200:
            logs = response.json()
        else:
            flash("Kunne ikke hente logs fra API")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return render_template(
        "admin_logs.html",
        logs=logs
    )


@app.route("/admin/logs/create", methods=["POST"])
@admin_required
def admin_create_log():
    user_id = request.form.get("user_id")
    device = request.form.get("device")
    used_method = request.form.get("used_method")
    access_granted = request.form.get("access_granted") == "true"
    result = request.form.get("result")
    security_picture = request.files.get("security_picture")

    try:
        data = {
            "user_id": user_id,
            "device": device,
            "used_method": used_method,
            "access_granted": "true" if access_granted else "false",
            "result": result
        }

        files = None

        if security_picture and security_picture.filename:
            files = {
                "file": (
                    security_picture.filename,
                    security_picture.stream,
                    security_picture.mimetype
                )
            }

        response = requests.post(
            f"{API_BASE_URL}/logs",
            data=data,
            files=files,
            timeout=5
        )

        if response.status_code == 201:
            flash("Log blev oprettet")
        else:
            flash(f"Log kunne ikke oprettes: {response.text}")

    except requests.exceptions.RequestException as e:
        flash(f"Kunne ikke forbinde til API-serveren: {e}")

    return redirect(url_for("admin_logs"))


@app.route("/admin/logs/delete/<int:log_id>", methods=["POST"])
@admin_required
def admin_delete_log(log_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/logs/{log_id}",
            timeout=5
        )

        if response.status_code == 200:
            flash("Log blev slettet")
        else:
            flash(f"Log kunne ikke slettes: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_logs"))

# Admin face routes
@app.route("/admin/faces")
@admin_required
def admin_faces():
    faces = []

    try:
        response = requests.get(
            f"{API_BASE_URL}/faces",
            timeout=5
        )

        if response.status_code == 200:
            faces = response.json()
        else:
            flash("Kunne ikke hente faces fra API")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return render_template(
        "admin_faces.html",
        faces=faces
    )


@app.route("/admin/faces/create", methods=["POST"])
@admin_required
def admin_create_face():
    user_id = request.form.get("user_id")
    face_encoding = request.form.get("face_encoding")
    is_active = request.form.get("is_active") == "true"
    face_picture_path = request.files.get("face_picture_path")
    face_picture = request.files.get("face_picture")


    try:
        data = {
            "user_id": user_id,
            "face_encoding": face_encoding,
            "is_active": is_active,
            "face_picture_path": face_picture_path
        }

        files = None

        if face_picture and face_picture.filename:
            files = {
                "file": (
                    face_picture.filename,
                    face_picture.stream,
                    face_picture.mimetype
                )
            }

        response = requests.post(
            f"{API_BASE_URL}/faces",
            data=data,
            files=files,
            timeout=5
        )

        if response.status_code == 201:
            flash("Face blev oprettet")
        else:
            flash(f"Face kunne ikke oprettes: {response.text}")

    except requests.exceptions.RequestException as e:
        flash(f"Kunne ikke forbinde til API-serveren: {e}")

    return redirect(url_for("admin_faces"))

@app.route("/admin/faces/delete/<int:face_id>", methods=["POST"])
@admin_required
def admin_delete_face(face_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/faces/{face_id}",
            timeout=5
        )

        if response.status_code == 200:
            flash("Face blev slettet")
        else:
            flash(f"Face kunne ikke slettes: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_faces"))

@app.route("/faces/update/<int:face_id>", methods=["POST"])
@login_required
def update_face_image(face_id):
    file = request.files.get("file")

    if file is None or file.filename == "":
        flash("Du skal vælge et billede")
        return redirect(url_for("dashboard"))

    try:
        is_active = is_admin()

        data = {
            "is_active": "true" if is_active else "false"
        }

        files = {
            "file": (
                file.filename,
                file.stream,
                file.mimetype
            )
        }

        response = requests.patch(
            f"{API_BASE_URL}/faces/{face_id}",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code == 200:
            if is_active:
                flash("Face billede blev opdateret og aktiveret")
            else:
                flash("Face billede blev opdateret og afventer admin godkendelse")
        else:
            flash(f"Opdatering fejlede: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("dashboard"))

# Admin pin routes
@app.route("/admin/pins")
@admin_required
def admin_pins():
    pins = []

    try:
        response = requests.get(
            f"{API_BASE_URL}/pins",
            timeout=5
        )

        if response.status_code == 200:
            pins = response.json()
        else:
            flash("Kunne ikke hente pins fra API")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return render_template(
        "admin_pins.html",
        pins=pins
    )


@app.route("/admin/pins/create", methods=["POST"])
@admin_required
def admin_create_pin():
    user_id = request.form.get("user_id")
    pin_code = request.form.get("pin_code")
    expiry_date = request.form.get("expiry_date")
    is_active = request.form.get("is_active") == "true"


    try:
        data = {
            "user_id": user_id,
            "pin_code": pin_code,
            "expires_at": expiry_date,
            "is_active": is_active
        }


        response = requests.post(
            f"{API_BASE_URL}/pins",
            json=data,
            timeout=5
        )

        if response.status_code == 201:
            flash("Pin blev oprettet")
        else:
            flash(f"Pin  kunne ikke oprettes: {response.text}")

    except requests.exceptions.RequestException as e:
        flash(f"Kunne ikke forbinde til API-serveren: {e}")

    return redirect(url_for("admin_pins"))


@app.route("/admin/pins/delete/<int:pin_id>", methods=["POST"])
@admin_required
def admin_delete_pin(pin_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/pins/{pin_id}",
            timeout=5
        )

        if response.status_code == 200:
            flash("Pin blev slettet")
        else:
            flash(f"Pin kunne ikke slettes: {response.text}")

    except requests.exceptions.RequestException:
        flash("Kunne ikke forbinde til API-serveren")

    return redirect(url_for("admin_pins"))

if __name__ == "__main__":
    create_tables()
    seed_data()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        threaded=True
    )