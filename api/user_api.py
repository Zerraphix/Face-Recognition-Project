from flask import request
# https://flask-restx.readthedocs.io/en/latest/swagger.html Bedre visuel api dokumentation
# https://flask-restx.readthedocs.io/en/latest/scaling.html#multiple-namespaces Deler dem op i flere filer alligvel og samler dem i app.py
from flask_restx import Namespace, Resource, fields


from services.security_service import hash_pass
from database.user_db import get_all_users, get_user_by_id, create_user, delete_user


api_user = Namespace("users", description="User operations")


user_model = api_user.model("User", {
    "user_id": fields.Integer,
    "first_name": fields.String,
    "last_name": fields.String,
    "email": fields.String,
    "password_hash": fields.String,
    "role_id": fields.Integer,
    "role_name": fields.String
})


create_user_model = api_user.model("CreateUser", {
    "first_name": fields.String(required=True, example="Test"),
    "last_name": fields.String(required=True, example="Testerson"),
    "email": fields.String(required=True, example="test@example.com"),
    "password_hash": fields.String(required=True, example="password"),
    "role_id": fields.Integer(required=True, example=1)
})


@api_user.route("")
class UserList(Resource):

    @api_user.marshal_list_with(user_model)
    def get(self):
        return get_all_users()


    @api_user.expect(create_user_model)
    @api_user.marshal_with(user_model, code=201)
    def post(self):
        data = request.get_json()

        required_fields = [
            "first_name",
            "last_name",
            "email",
            "password_hash",
            "role_id"
        ]

        for field in required_fields:
            if field not in data:
                api_user.abort(400, f"Missing field: {field}")

        try:
            password_hash = hash_pass(data["password_hash"])

            new_user = create_user(
                data["first_name"],
                data["last_name"],
                data["email"],
                password_hash,
                data["role_id"]
            )

            return new_user, 201

        except Exception as e:
            api_user.abort(400, str(e))


@api_user.route("/<int:user_id>")
class UserById(Resource):

    @api_user.marshal_with(user_model)
    def get(self, user_id):
        user = get_user_by_id(user_id)

        if user is None:
            api_user.abort(404, "User not found")

        return user


    def delete(self, user_id):
        deleted = delete_user(user_id)

        if not deleted:
            api_user.abort(404, "User not found")

        return {"message": "User deleted"}, 200