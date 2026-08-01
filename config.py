# config.py
#
# This file is the single source of truth for our Flask app and every
# extension instance (db, bcrypt, jwt, api). Models, schemas, and routes
# all import from here instead of creating their own instances -- this


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

# Where our SQLite database file lives. 
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

# --- Shared extension instances ---
db = SQLAlchemy(app)          # ORM: lets us define models as Python classes
bcrypt = Bcrypt(app)          # Password hashing
jwt = JWTManager(app)         # Issues + verifies JWTs
api = Api(app)                # flask-restful: lets us register Resource classes
migrate = Migrate(app, db)    # Enables `flask db migrate` / `flask db upgrade`

# Allow our React dev server (running on a different port) to call this API.
CORS(app)