
#   UserSchema    -> OUTPUT. Turns a User model into JSON. Deliberately
#                    only exposes id + username -- password_hash must
#                    never be serialized back to the client.
#   SignupSchema  -> INPUT. Validates the body of POST /signup before we
#                    touch the database (username length, password
#                    strength, and that the two password fields match).
#   LoginSchema   -> INPUT. Validates the body of POST /login (lighter
#                    checks -- we don't need password strength rules
#                    here, just that both fields were provided).

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class UserSchema(Schema):
    id = fields.Int(dump_only=True)  # dump_only = never accepted as input, only returned
    username = fields.Str(required=True)


class SignupSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(
            min=3, max=20, error="Username must be between 3 and 20 characters."
        ),
    )
    password = fields.Str(
        required=True,
        load_only=True,  # never serialize a password back out, even by mistake
        validate=validate.Length(
            min=6, error="Password must be at least 6 characters."
        ),
    )
    password_confirmation = fields.Str(required=True, load_only=True)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Runs after the individual field validators above. Cross-field
        checks (comparing two fields to each other) have to happen here
        rather than on a single field, since a single field's validator
        only ever sees its own value."""
        if data.get("password") != data.get("password_confirmation"):
            raise ValidationError(
                "Passwords must match.", field_name="password_confirmation"
            )


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)