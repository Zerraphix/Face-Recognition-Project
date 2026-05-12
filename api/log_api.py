from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage
from datetime import datetime


from services.file_upload import save_uploaded_file
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

create_log_parser = reqparse.RequestParser()
create_log_parser.add_argument("user_id", type=int, required=True, location="form")
create_log_parser.add_argument("device", type=str, required=True, location="form")
create_log_parser.add_argument("used_method", type=str, required=True, location="form")
create_log_parser.add_argument("access_granted", type=bool, required=True, location="form")
create_log_parser.add_argument("result", type=str, required=True, location="form")
create_log_parser.add_argument("security_picture_path", type=str, required=False, location="form")
create_log_parser.add_argument("file", type=FileStorage, required=False, location="files")



@api_log.route("")
class LogList(Resource):

    @api_log.marshal_list_with(log_model)
    def get(self):
        return get_all_logs()


    @api_log.expect(create_log_parser)
    @api_log.marshal_with(log_model, code=201)
    def post(self):
        args = create_log_parser.parse_args()

        user_id = args["user_id"]
        device = args["device"]
        used_method = args["used_method"]
        access_granted = args["access_granted"]
        result = args["result"]
        security_picture_path = args.get("security_picture_path")
        file = args["file"]

        
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        try:
            if file:
                db_path = save_uploaded_file(
                file=file,
                upload_folder="uploads/logs",
                preferred_name=filename
            )
            else:
                db_path = security_picture_path
            

            new_log = create_log(
                user_id,
                device,
                used_method,
                access_granted,
                result,
                db_path
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