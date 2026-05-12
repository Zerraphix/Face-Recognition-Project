from flask import request
# https://flask-restx.readthedocs.io/en/latest/parsing.html Brugt til formdata parsing, især til fil uploads
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from services.file_upload import save_uploaded_file
from database.face_db import get_all_faces, get_face_by_id, create_face, delete_face


api_face = Namespace("faces", description="Face operations")


face_model = api_face.model("Face", {
    "face_id": fields.Integer,
    "user_id": fields.Integer,
    "created_at": fields.String,
    "face_encoding": fields.String,
    "face_picture_path": fields.String,
    "is_active": fields.Boolean,
    "first_name": fields.String,
    "last_name": fields.String,
    "email": fields.String,
    "role_id": fields.Integer,
    "role_name": fields.String
})


create_face_parser = reqparse.RequestParser()
create_face_parser.add_argument("user_id", type=int, required=True, location="form")
create_face_parser.add_argument("face_encoding", type=str, required=True, location="form")
create_face_parser.add_argument("is_active", type=bool, required=True, location="form")
create_face_parser.add_argument("file", type=FileStorage, required=True, location="files")

@api_face.route("")
class FaceList(Resource):

    @api_face.marshal_list_with(face_model)
    def get(self):
        return get_all_faces()

    @api_face.expect(create_face_parser)
    @api_face.marshal_with(face_model, code=201)
    def post(self):
        args = create_face_parser.parse_args()

        user_id = args["user_id"]
        face_encoding = args["face_encoding"]
        is_active = args["is_active"]
        file = args["file"]

        try:
            db_path = save_uploaded_file(
                file=file,
                upload_folder="uploads/faces",
                preferred_name=f"{user_id}.jpg"
            )

            new_face = create_face(
                user_id,
                face_encoding,
                db_path,
                is_active
            )

            return new_face, 201

        except ValueError as e:
            api_face.abort(400, str(e))

        except Exception as e:
            api_face.abort(500, str(e))


@api_face.route("/<int:face_id>")
class FaceById(Resource):

    @api_face.marshal_with(face_model)
    def get(self, face_id):
        face = get_face_by_id(face_id)

        if face is None:
            api_face.abort(404, "Face not found")

        return face
    
    def delete(self, face_id):
        deleted = delete_face(face_id)

        if not deleted:
            api_face.abort(404, "Face not found")

        return {"message": "Face deleted"}, 200