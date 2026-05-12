from flask import request
from flask_restx import Namespace, Resource, fields


from database.log_db import get_all_logs, get_log_by_id, create_log, delete_log


api_log = Namespace("logs", description="Log operations")


log_model = api_log.model("Log", {
    "log_id": fields.Integer,
    "user_id": fields.Integer,
    "device": fields.String,
    "used_method": fields.String,
    "timestamp": fields.String,
    "access_granted": fields.Boolean,
    "result": fields.String,
    "security_picture_path": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "role_name": fields.String
})


create_log_model = api_log.model("CreateLog", {
    "user_id": fields.Integer(required=True, example=1),
    "device": fields.String(required=True, example="Test Device"),
    "used_method": fields.String(required=True, example="Test Method"),
    "access_granted": fields.Boolean(required=True, example=True),
    "result": fields.String(required=True, example="Test Result"),
    "security_picture_path": fields.String(required=True, example="/path/to/security/picture.jpg")
})


@api_log.route("")
class LogList(Resource):

    @api_log.marshal_list_with(log_model)
    def get(self):
        return get_all_logs()


    @api_log.expect(create_log_model)
    @api_log.marshal_with(log_model, code=201)
    def post(self):
        data = request.get_json()

        required_fields = [
            "user_id",
            "device",
            "used_method",
            "access_granted",
            "result",
            "security_picture_path"
        ]

        for field in required_fields:
            if field not in data:
                api_log.abort(400, f"Missing field: {field}")

        try:
            new_log = create_log(
                data["user_id"],
                data["device"],
                data["used_method"],
                data["access_granted"],
                data["result"],
                data["security_picture_path"]
            )

            return new_log, 201

        except Exception as e:
            api_log.abort(400, str(e))


@api_log.route("/<int:log_id>")
class LogById(Resource):

    @api_log.marshal_with(log_model)
    def get(self, log_id):
        log = get_log_by_id(log_id)

        if log is None:
            api_log.abort(404, "Log not found")

        return log


    def delete(self, log_id):
        deleted = delete_log(log_id)

        if not deleted:
            api_log.abort(404, "Log not found")

        return {"message": "Log deleted"}, 200