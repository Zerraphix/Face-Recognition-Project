from flask import request
from flask_restx import Namespace, Resource, fields


from services.security_service import hash_pass, verify_pass
from database.user_db import get_all_users, get_user_by_id, get_user_by_email, create_user, delete_user, update_user


api_user = Namespace("users", description="User operations")


user_model = api_user.model("User", {
    "user_id": fields.Integer,
    "first_name": fields.String,
    "last_name": fields.String,
    "email": fields.String,
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

update_user_model = api_user.model("UpdateUser", {
    "first_name": fields.String(required=False, example="Test"),
    "last_name": fields.String(required=False, example="Testerson"),
    "email": fields.String(required=False, example="test@example.com"),
    "password_hash": fields.String(required=False, example="password"),
    "role_id": fields.Integer(required=False, example=1)
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
    
    @api_user.expect(update_user_model)
    @api_user.marshal_with(user_model, code=201)
    def put(self, user_id):
        data = request.get_json()

        if data is None:
            api_user.abort(400, "Missing JSON body")

        try:
            password_hash = None

            if "password" in data:
                if data["password"] is not None and data["password"] != "":
                    password_hash = hash_pass(data["password"])

            updated_user = update_user(
                user_id=user_id,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                email=data.get("email"),
                password_hash=password_hash,
                role_id=data.get("role_id")
            )

            if updated_user is None:
                api_user.abort(404, "User not found")

            return updated_user, 200

        except Exception as e:
            api_user.abort(400, str(e))
        
    

login_model = api_user.model("UserLogin", {
    "email": fields.String(required=True, example="test@example.com"),
    "password": fields.String(required=True, example="password")
})

@api_user.route("/login", methods=["POST"])
class UserLogin(Resource):

    @api_user.expect(login_model)
    def post(self):
        data = request.get_json()

        if "email" not in data or "password" not in data:
            api_user.abort(400, "Missing email or password")

        user = get_user_by_email(data["email"])

        if user is None:
            api_user.abort(404, "User not found")

        if not verify_pass(data["password"], user["password_hash"]):
            api_user.abort(401, "Invalid password")

        return {
            "message": "Login successful",
            "user_id": user["user_id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
            "role_id": user["role_id"],
            "role_name": user["role_name"],
            "has_face_data": bool(user["has_face_data"])
        }, 200