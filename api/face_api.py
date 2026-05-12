from flask import request
from flask_restx import Namespace, Resource, fields


from database.face_db import get_all_faces, get_face_by_id, create_face, delete_face


api_face = Namespace("faces", description="Face operations")


face_model = api_face.model("Face", {
    "face_id": fields.Integer,
    "user_id": fields.Integer,
    "created_at": fields.String,
    "face_encoding": fields.String,
    "face_picture_path": fields.String,
    "is_active": fields.Boolean
})


create_face_model = api_face.model("CreateFace", {
    "user_id": fields.Integer(required=True, example=1),
    "face_encoding": fields.String(required=True, example="Test Face Encoding"),
    "face_picture_path": fields.String(required=True, example="/path/to/face/picture.jpg"),
        "is_active": fields.Boolean(required=True, example=True)
})



@api_face.route("")
class FaceList(Resource):

    @api_face.marshal_list_with(face_model)
    def get(self):
        return get_all_faces()


    @api_face.expect(create_face_model)
    @api_face.marshal_with(face_model, code=201)
    def post(self):
        data = request.get_json()

        required_fields = [
            "user_id",
            "face_encoding",
            "face_picture_path",
            "is_active"
        ]

        for field in required_fields:
            if field not in data:
                api_face.abort(400, f"Missing field: {field}")

        try:
            new_face = create_face(
                data["user_id"],
                data["face_encoding"],
                data["face_picture_path"],
                data["is_active"]
            )

            return new_face, 201

        except Exception as e:
            api_face.abort(400, str(e))


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