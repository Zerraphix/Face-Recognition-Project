from flask import request
from flask_restx import Namespace, Resource, fields
from datetime import datetime


from services.security_service import hash_pass, verify_pass
from database.pin_db import get_active_pins, get_all_pins, get_pin_by_id, create_pin, delete_pin


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
    "is_active": fields.String(required=True, example="true")
})



verify_pin_model = api_pin.model("VerifyPin", {
    "pin_code": fields.String(required=True, example="12345678")
})


verify_pin_response_model = api_pin.model("VerifyPinResponse", {
    "approved": fields.Boolean,
    "user_id": fields.Integer,
    "pin_id": fields.Integer,
    "result": fields.String
})

def parse_expires_at(value):
    if value is None:
        api_pin.abort(400, "expires_at må ikke være None")

    if not isinstance(value, str):
        api_pin.abort(400, "expires_at skal være en string")

    value = value.strip()

    if value == "" or value.lower() == "none":
        api_pin.abort(400, "expires_at må ikke være tom eller None")

    accepted_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]

    for date_format in accepted_formats:
        try:
            parsed_date = datetime.strptime(value, date_format)

            # Hvis man kun sender dato, sæt udløb til slutningen af dagen
            if date_format == "%Y-%m-%d":
                parsed_date = parsed_date.replace(hour=23, minute=59, second=59)

            # SQLite-venligt format
            return parsed_date.strftime("%Y-%m-%d %H:%M:%S")

        except ValueError:
            pass

    api_pin.abort(
        400,
        "Invalid expires_at format. Brug fx '2026-12-31 23:59:59' eller HTML datetime-local format '2026-12-31T23:59'"
    )

def convert_is_active(value):
    if value == "true":
        return True

    if value == "false":
        return False

    else:
        return False
    
@api_pin.route("")
class PinList(Resource):

    @api_pin.marshal_list_with(pin_model)
    def get(self):
        return get_all_pins()


    @api_pin.expect(create_pin_model)
    @api_pin.marshal_with(pin_model, code=201)
    def post(self):
        data = request.get_json()

        if data is None:
            api_pin.abort(400, "Missing JSON body")

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
            expires_at = parse_expires_at(data["expires_at"])
            pin_code_hash = hash_pass(data["pin_code"])

            new_pin = create_pin(
                data["user_id"],
                pin_code_hash,
                expires_at,
                convert_is_active(data["is_active"])
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

@api_pin.route("/verify")
class PinVerify(Resource):

    @api_pin.expect(verify_pin_model)
    @api_pin.marshal_with(verify_pin_response_model)
    def post(self):
        data = request.get_json()

        if data is None:
            api_pin.abort(400, "Missing JSON body")

        pin_code = data.get("pin_code")

        if not pin_code:
            api_pin.abort(400, "Missing field: pin_code")

        if not pin_code.isdigit():
            api_pin.abort(400, "pin_code must only contain numbers")

        try:
            active_pins = get_active_pins()

            for pin in active_pins:
                pin_code_hash = pin["pin_code_hash"]

                if verify_pass(pin_code, pin_code_hash):
                    return {
                        "approved": True,
                        "user_id": pin["user_id"],
                        "pin_id": pin["pin_id"],
                        "result": "PIN accepted"
                    }, 200

            return {
                "approved": False,
                "user_id": None,
                "pin_id": None,
                "result": "Invalid, inactive or expired PIN"
            }, 200

        except Exception as e:
            api_pin.abort(500, str(e))
