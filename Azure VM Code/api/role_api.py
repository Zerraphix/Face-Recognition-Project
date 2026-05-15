from flask_restx import Namespace, Resource, fields
from database.role_db import get_all_roles, get_role_by_id


api_role = Namespace("roles", description="Role operations")


role_model = api_role.model("Role", {
    "role_id": fields.Integer,
    "role_name": fields.String
})


@api_role.route("")
class RoleList(Resource):

    @api_role.marshal_list_with(role_model)
    def get(self):
        return get_all_roles()


@api_role.route("/<int:role_id>")
class RoleById(Resource):

    @api_role.marshal_with(role_model)
    def get(self, role_id):
        role = get_role_by_id(role_id)

        if role is None:
            api_role.abort(404, "Role not found")

        return role