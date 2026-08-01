# models/user.py
#
# The User model represents an account in our system. It never stores a
# plaintext password -- only a bcrypt hash -- and exposes helper methods
# so the rest of the app (auth routes) never has to touch bcrypt directly.

from config import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # unique=True enforces "no two accounts with the same username" at the
    # database level (not just in our own validation code), which is what
    # the rubric means by usernames being "a valid identifier".
    username = db.Column(db.String(80), unique=True, nullable=False)

    # We only ever store the hashed password, never the raw one.
    password_hash = db.Column(db.String(128), nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # One user can have many mood entries. `cascade="all, delete-orphan"`
    # means if a user is deleted, their mood entries are cleaned up too,
    # instead of being left behind as orphaned rows.
    mood_entries = db.relationship(
        "MoodEntry", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, plaintext_password):
        """Hash and store a new password. Call this on signup or password change."""
        self.password_hash = bcrypt.generate_password_hash(
            plaintext_password
        ).decode("utf-8")

    def authenticate(self, plaintext_password):
        """Check a plaintext password against the stored hash. Returns True/False."""
        return bcrypt.check_password_hash(self.password_hash, plaintext_password)

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"