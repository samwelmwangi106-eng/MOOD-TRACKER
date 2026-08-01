# app.py
#
# This is where everything else (config, models, schemas) comes together
# as actual HTTP endpoints. Each Resource class below maps to one URL,
# with one method per HTTP verb (get/post/patch/delete) -- this is the
# flask-restful pattern instead of a pile of @app.route functions.

from flask import request, jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from marshmallow import ValidationError

from config import app, db, api
from models import User, MoodEntry
from schemas import (
    UserSchema,
    SignupSchema,
    LoginSchema,
    mood_entry_schema,
    mood_entries_schema,
)

user_schema = UserSchema()
signup_schema = SignupSchema()
login_schema = LoginSchema()



# Auth routes


class Signup(Resource):
    """POST /signup -- create a new account and log the user straight in."""

    def post(self):
        json_data = request.get_json(silent=True) or {}

        # Validate shape/content of the request body BEFORE touching the
        # database at all (length rules, password match, etc).
        try:
            data = signup_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        # Enforce uniqueness ourselves first so we can return a clean,
        # specific error message instead of letting a raw database
        # IntegrityError bubble up if two people happen to race each
        # other for the same username.
        if User.query.filter_by(username=data["username"]).first():
            return {"errors": ["Username is already taken."]}, 409

        user = User(username=data["username"])
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()

        # identity must be a string -- flask-jwt-extended expects the
        # "sub" claim to be a string, and will error on a raw int here.
        token = create_access_token(identity=str(user.id))

        return make_response(
            jsonify(token=token, user=user_schema.dump(user)), 201
        )


class Login(Resource):
    """POST /login -- authenticate an existing user."""

    def post(self):
        json_data = request.get_json(silent=True) or {}

        try:
            data = login_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        user = User.query.filter_by(username=data["username"]).first()

        # Same error message whether the username doesn't exist or the
        # password is wrong -- this avoids confirming to an attacker
        # which usernames are actually registered.
        if not user or not user.authenticate(data["password"]):
            return {"errors": ["Invalid username or password."]}, 401

        token = create_access_token(identity=str(user.id))

        return make_response(
            jsonify(token=token, user=user_schema.dump(user)), 200
        )


class Me(Resource):
    """GET /me -- return the currently authenticated user.

    This is what the frontend calls on page load to check whether the
    token in localStorage is still valid and, if so, who's logged in.
    """

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user:
            # Token is valid but the user it points to no longer exists
            # (e.g. deleted account) -- treat as unauthenticated.
            return {"errors": ["User not found."]}, 404

       
        return user_schema.dump(user), 200



# MoodEntry routes


def get_owned_entry_or_error(entry_id, user_id):
    """Shared ownership check used by every single-entry route below.

    Returns (entry, None) on success, or (None, (body, status)) on
    failure -- callers just do:
        entry, error = get_owned_entry_or_error(id, user_id)
        if error:
            return error
    This keeps the 403-vs-404 logic defined in exactly one place instead
    of repeated (and potentially drifting) across GET/PATCH/DELETE.
    """
    entry = MoodEntry.query.get(entry_id)

    if entry is None:
        return None, ({"errors": ["Mood entry not found."]}, 404)

    if entry.user_id != int(user_id):
        
        return None, ({"errors": ["You do not have access to this mood entry."]}, 403)

    return entry, None


class MoodEntryList(Resource):
    """GET  /mood_entries -- paginated list of the current user's entries
    POST /mood_entries -- create a new entry owned by the current user
    """

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # Pagination params come from the query string, e.g.
        # /mood_entries?page=2&per_page=5. We fall back to sane defaults
        # and clamp per_page so a client can't request an enormous page.
        try:
            page = int(request.args.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(request.args.get("per_page", 10))
        except (TypeError, ValueError):
            per_page = 10
        page = max(page, 1)
        per_page = max(1, min(per_page, 50))

        query = (
            MoodEntry.query.filter_by(user_id=int(user_id))
            .order_by(MoodEntry.created_at.desc())
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "mood_entries": mood_entries_schema.dump(pagination.items),
            "meta": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }, 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        json_data = request.get_json(silent=True) or {}

        try:
            data = mood_entry_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        entry = MoodEntry(
            user_id=int(user_id),
            mood=data["mood"],
            note=data.get("note"),
        )
        db.session.add(entry)
        db.session.commit()

        return mood_entry_schema.dump(entry), 201


class MoodEntryDetail(Resource):
    """GET/PATCH/DELETE /mood_entries/<id> -- single entry, owner only."""

    @jwt_required()
    def get(self, entry_id):
        user_id = get_jwt_identity()
        entry, error = get_owned_entry_or_error(entry_id, user_id)
        if error:
            return error
        return mood_entry_schema.dump(entry), 200

    @jwt_required()
    def patch(self, entry_id):
        user_id = get_jwt_identity()
        entry, error = get_owned_entry_or_error(entry_id, user_id)
        if error:
            return error

        json_data = request.get_json(silent=True) or {}
        try:
            # partial=True: a PATCH can send just `note`, just `mood`,
            # or both -- nothing is required that isn't actually present.
            data = mood_entry_schema.load(json_data, partial=True)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        if "mood" in data:
            entry.mood = data["mood"]
        if "note" in data:
            entry.note = data["note"]

        db.session.commit()
        return mood_entry_schema.dump(entry), 200

    @jwt_required()
    def delete(self, entry_id):
        user_id = get_jwt_identity()
        entry, error = get_owned_entry_or_error(entry_id, user_id)
        if error:
            return error

        db.session.delete(entry)
        db.session.commit()
        return "", 204


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(Me, "/me")
api.add_resource(MoodEntryList, "/mood_entries")
api.add_resource(MoodEntryDetail, "/mood_entries/<int:entry_id>")


if __name__ == "__main__":
    app.run(port=5000, debug=True)