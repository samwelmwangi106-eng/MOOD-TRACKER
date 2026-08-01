
# This file is the single source of truth for our Flask app and every
# extension instance (db, bcrypt, jwt, api). Models, schemas, and routes
# all import from here instead of creating their own instances -- this
# avoids circular imports and makes sure everyone is talking to the same
# database connection / app config.

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_migrate import Migrate
from flask_cors import CORS

# --- App setup ---
app = Flask(__name__)

# Where our SQLite database file lives. In production you'd swap this for
# a real DATABASE_URL (e.g. Postgres) via an environment variable.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///app.db"
)
# Turns off a SQLAlchemy feature we don't need (event tracking on every
# change) that otherwise adds overhead and a startup warning.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Secret key used to sign JWTs. In production this MUST come from an
# environment variable and never be committed to source control.
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "dev-secret-change-me"
)

# Flask-RESTful normally catches ANY exception raised inside a Resource
# method and turns it into a generic 500, before Flask itself ever gets a
# chance to check our custom error handlers below (e.g. the JWT ones).
# Setting this makes Flask-RESTful re-raise exceptions it doesn't
# recognize as HTTP errors, so they reach Flask's real handler chain --
# which is what lets our @jwt.unauthorized_loader etc. actually fire.
app.config["PROPAGATE_EXCEPTIONS"] = True

# --- Shared extension instances ---
db = SQLAlchemy(app)          # ORM: lets us define models as Python classes
bcrypt = Bcrypt(app)          # Password hashing
jwt = JWTManager(app)         # Issues + verifies JWTs
api = Api(app)                # flask-restful: lets us register Resource classes
migrate = Migrate(app, db)    # Enables `flask db migrate` / `flask db upgrade`

# Allow our React dev server (running on a different port) to call this API.
CORS(app)


# --- JWT error handlers ---
#
# By default, flask-jwt-extended raises exceptions (e.g.
# NoAuthorizationError) when a token is missing/invalid/expired. If we
# don't handle these ourselves, Flask's generic error handler catches
# them and returns a bare 500 Internal Server Error -- which is both the
# wrong status code (it's a client auth problem, not a server bug) and
# unhelpful for the frontend to work with. These callbacks make sure
# every one of those cases returns a clean 401 with a JSON body instead.

@jwt.unauthorized_loader
def missing_token_callback(reason):
    """No Authorization header was sent at all."""
    return {"errors": ["Missing or invalid authorization token."]}, 401


@jwt.invalid_token_loader
def invalid_token_callback(reason):
    """An Authorization header was sent, but the token is malformed/invalid."""
    return {"errors": ["Invalid authorization token."]}, 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """The token was valid but has expired."""
    return {"errors": ["Authorization token has expired."]}, 401