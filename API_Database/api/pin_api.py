from flask import request
from flask_restx import Namespace, Resource, fields


from services.security_service import hash_pass
from database.pin_db import get_all_pins, get_pin_by_id, create_pin, delete_pin


api_pin = Namespace("pins", description="Pin operations")


pin_model = api_pin.model("Pin", {
    "pin_id": fields.Integer,
    "user_id": fields.Integer,
    "pin_code_hash": fields.String,
    "expires_at": fields.String,
    "is_active": fields.Boolean,
    "first_name": fields.String,
    "last_name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "role_name": fields.String
})


create_pin_model = api_pin.model("CreatePin", {
    "user_id": fields.Integer(required=True, example=1),
    "pin_code": fields.String(required=True, example="12345678"),
    "expires_at": fields.String(required=True, example="2023-12-31 23:59:59"),
    "is_active": fields.Boolean(required=True, example=True)
})


@api_pin.route("")
class PinList(Resource):

    @api_pin.marshal_list_with(pin_model)
    def get(self):
        return get_all_pins()


    @api_pin.expect(create_pin_model)
    @api_pin.marshal_with(pin_model, code=201)
    def post(self):
        data = request.get_json()

        required_fields = [
            "user_id",
            "pin_code",
            "expires_at",
            "is_active"
        ]

        for field in required_fields:
            if field not in data:
                api_pin.abort(400, f"Missing field: {field}")

        try:
            pin_code_hash = hash_pass(data["pin_code"])

            new_pin = create_pin(
                data["user_id"],
                pin_code_hash,
                data["expires_at"],
                data["is_active"]
            )

            return new_pin, 201

        except Exception as e:
            api_pin.abort(400, str(e))


@api_pin.route("/<int:pin_id>")
class PinById(Resource):

    @api_pin.marshal_with(pin_model)
    def get(self, pin_id):
        pin = get_pin_by_id(pin_id)

        if pin is None:
            api_pin.abort(404, "Pin not found")

        return pin


    def delete(self, pin_id):
        deleted = delete_pin(pin_id)

        if not deleted:
            api_pin.abort(404, "Pin not found")

        return {"message": "Pin deleted"}, 200

