
# One schema covers both directions for MoodEntry:
#   - dump (model -> JSON): includes every field, including the
#     server-generated ones (id, user_id, timestamps).
#   - load (JSON -> validated data): only `mood` and `note` are ever
#     accepted from the client. `id`, `user_id`, and the timestamps are
#     dump_only -- if a client tries to send any of them (e.g. to fake a
#     different user_id and claim someone else's data), marshmallow
#     rejects the whole request with an 'Unknown field' validation error
#     rather than silently accepting or ignoring it. Ownership (user_id)
#     is only ever set server-side from the JWT identity in the route.

from marshmallow import Schema, fields, validate

from models.mood_entry import MOOD_CHOICES


class MoodEntrySchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)

    mood = fields.Str(
        required=True,
        validate=validate.OneOf(
            MOOD_CHOICES,
            error=f"Mood must be one of: {', '.join(MOOD_CHOICES)}.",
        ),
    )
    note = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000, error="Note must be 1000 characters or fewer."),
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# Shared instances so routes don't need to instantiate a new schema on
# every request. For PATCH (partial updates), routes call
# mood_entry_schema.load(data, partial=True) so `mood` isn't required
# when the client is only updating `note` (or vice versa).
mood_entry_schema = MoodEntrySchema()
mood_entries_schema = MoodEntrySchema(many=True)