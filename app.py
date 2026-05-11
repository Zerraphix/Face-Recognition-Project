from flask import Flask
# https://flask-restx.readthedocs.io/en/latest/
from flask_restx import Api

from database.init_db import create_tables, seed_data
from api.role_api import api_role
from api.user_api import api_user


app = Flask(__name__)

api = Api(
    app,
    title="Face Access API",
    version="1.0",
    description="API til ansigtsgenkendelse og adgangskontrol",
    doc="/docs"
)


api.add_namespace(api_role, path="/api/roles")
api.add_namespace(api_user, path="/api/users")


if __name__ == "__main__":
    create_tables()
    seed_data()
    app.run(debug=True)