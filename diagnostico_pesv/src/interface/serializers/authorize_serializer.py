from marshmallow import Schema, fields
from marshmallow.decorators import post_dump, post_load
from marshmallow.exceptions import ValidationError


class UserSerializer(Schema):
    id = fields.Integer(required=True)
    username = fields.String(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)
    licensia_sst = fields.String(required=True)
    cedula = fields.String(required=True)
    avatar = fields.String(required=True)

    def load(self, data: dict) -> dict:
        try:
            data = super().load(data)
        except ValidationError as err:
            data = {"errors": err.messages}
        return data
