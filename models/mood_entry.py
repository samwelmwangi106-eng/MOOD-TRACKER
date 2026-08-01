# models/mood_entry.py
#
# A single mood log entry belonging to exactly one user. Ownership is
# enforced by the `user_id` foreign key -- every query in our routes will
# filter on this column so a user can never see or edit someone else's
# entries.

from config import db

# The fixed set of allowed mood values. Kept here (not just in the schema)
# so both the model and the validation layer can reference the same list
# instead of duplicating it in two places.
MOOD_CHOICES = ("great", "good", "okay", "low", "bad")


class MoodEntry(db.Model):
    __tablename__ = "mood_entries"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to the owning user. This is the column every ownership
    # check in our routes will filter by (e.g. .filter_by(user_id=...)).
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Plain String rather than a DB-level Enum: keeps the column forgiving
    # (easy to test in Postman) while marshmallow enforces the allowed
    # values at the API boundary, where validation errors are easier to
    # return as clean JSON than a raw database error would be.
    mood = db.Column(db.String(10), nullable=False)

    # Optional free-text reflection to go with the mood.
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # Automatically bumped by SQLAlchemy every time the row is updated.
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    def __repr__(self):
        return f"<MoodEntry id={self.id} user_id={self.user_id} mood={self.mood}>"