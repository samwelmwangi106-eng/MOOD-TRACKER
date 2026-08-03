# Mood Tracker API

A secure Flask backend for a personal mood-tracking app. Users can sign
up, log in, and privately log how they're feeling over time — each mood
entry belongs to exactly one user, and no user can ever view, edit, or
delete another user's entries.

Built for the **client-with-jwt** React frontend (JWT-based auth), but
works with any client that speaks JSON over HTTP (Postman, curl, etc).

## Features

- JWT authentication (signup, login, session persistence via `/me`)
- Passwords hashed with bcrypt — never stored or returned in plaintext
- A `MoodEntry` resource, fully owned by the user who created it
- Full CRUD on mood entries (`GET`, `POST`, `PATCH`, `DELETE`)
- Pagination on the mood entries index route
- Ownership enforcement: `403` if a mood entry exists but isn't yours,
  `404` if it doesn't exist at all
- Marshmallow validation on every input (usernames, passwords, mood
  values, note length)
- Faker-based seed script for quick manual testing

## Tech stack

Flask 2.2.2 · Flask-SQLAlchemy 3.0.3 · Flask-RESTful 0.3.9 ·
Flask-JWT-Extended · Flask-Bcrypt · Flask-Migrate · marshmallow ·
Faker · SQLite · Pipenv

## Project structure

```
config.py         # Flask app + shared extension instances (db, bcrypt, jwt, api)
app.py             # All routes (Signup, Login, Me, MoodEntry CRUD)
models/
  user.py           # User model, password hashing
  mood_entry.py      # MoodEntry model, owned by a user
schemas/
  user_schema.py      # Signup/Login validation, User output serialization
  mood_entry_schema.py # MoodEntry validation + serialization
seed.py             # Faker-based demo data
migrations/          # Flask-Migrate schema history
Pipfile / Pipfile.lock
```

## Installation

**Requirements:** Python **3.8.13 – 3.13** (Werkzeug 2.2.2, pinned by
this project, is incompatible with Python 3.14+ — see [Known
gotchas](#known-gotchas) below if you hit an `ast.Str` error).

### Installing Pipenv (if you don't have it yet)

**macOS / Linux:**
```bash
# Don't use `sudo apt install pipenv` -- it's often outdated on Debian/Ubuntu.
sudo apt install pipx -y
pipx ensurepath
# close and reopen your terminal, then:
pipx install pipenv
```
If `pipx` isn't available, this also works:
```bash
pip3 install --user pipenv --break-system-packages
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Windows:**
```bash
pip install pipenv
```

Confirm it worked: `pipenv --version`

### Installing Python 3.11 (if you don't have it yet)

**macOS / Linux (Ubuntu/Debian):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-distutils -y
```

**Windows:** download the Python 3.11.x installer from
[python.org/downloads](https://www.python.org/downloads/) (not the
newest version shown by default — find 3.11 in the release list) and
check "Add python.exe to PATH" during install.

Confirm it worked: `python3.11 --version` (Linux/Mac) or `py -0p`
(Windows, should list `3.11` with a path).

### Installing the project dependencies

```bash
git clone <your-repo-url>
cd MOOD-TRACKER

pipenv install --python 3.11   # or any 3.9-3.13 interpreter you have
pipenv install --dev           # installs pytest
```

> **If pipenv warns about a `python_version` other than 3.11** (e.g.
> `"Your Pipfile requires python_version 3.14..."`), open `Pipfile` and
> check the `[requires]` section at the bottom -- it should say
> `python_version = "3.11"`. If it says something else, that's a
> leftover from an earlier `pipenv install` run on a different machine
> that auto-wrote whatever Python was active at the time. Fix it with:
> ```bash
> sed -i 's/python_version = ".*"/python_version = "3.11"/' Pipfile
> pipenv lock
> git add Pipfile Pipfile.lock
> git commit -m "Fix Pipfile python_version pin"
> git push
> ```
> Push the fix so the next clone (another machine, a teammate, a
> grader) doesn't hit the same issue.

Set up the database:

```bash
FLASK_APP=app.py pipenv run flask db upgrade
```

(If `migrations/` doesn't exist yet in your clone, run
`flask db init` and `flask db migrate -m "Initial migration"` first.)

Seed some demo data:

```bash
pipenv run python seed.py
```

This creates a few demo accounts (see terminal output for exact
credentials — `alice` / `password123` and `bob` / `password123` by
default) plus a batch of Faker-generated mood entries for each.

## Running the app

```bash
pipenv run python app.py
```

The API runs at **`http://localhost:5555`**.

> This port is not arbitrary — it matches the `"proxy"` value in the
> `client-with-jwt` frontend's `package.json`. If you change it, update
> the frontend's proxy setting too, or the two won't be able to talk to
> each other.

### Running the frontend alongside it

```bash
cd client-with-jwt
npm install
PORT=4000 npx react-scripts start   # if `npm start` fails on Windows/Git Bash, use this form instead
```

Open `http://localhost:4000` — signup/login talk directly to this API
through the dev server's proxy.

## API Reference

All request/response bodies are JSON. Endpoints marked **** require
`Authorization: Bearer <token>`.

### Auth

| Method | Endpoint  |  | Description |
|--------|-----------|:--:|-------------|
| POST   | `/signup` |    | Create an account and log in immediately. Body: `{username, password, password_confirmation}`. Returns `{token, user}`. |
| POST   | `/login`  |    | Authenticate an existing user. Body: `{username, password}`. Returns `{token, user}`. |
| GET    | `/me`     |  | Return the currently authenticated user as `{id, username}`. Used by the frontend to persist login across page refreshes. |

### Mood Entries

| Method | Endpoint             |  | Description |
|--------|-----------------------|:--:|-------------|
| GET    | `/mood_entries`        |  | List the current user's mood entries, paginated. Query params: `page` (default 1), `per_page` (default 10, max 50). |
| POST   | `/mood_entries`        |  | Create a mood entry owned by the current user. Body: `{mood, note?}`. |
| GET    | `/mood_entries/<id>`   |  | Get a single mood entry. `403` if it belongs to another user, `404` if it doesn't exist. |
| PATCH  | `/mood_entries/<id>`   |  | Partially update a mood entry (`mood` and/or `note`). Same ownership rules as GET. |
| DELETE | `/mood_entries/<id>`   |  | Delete a mood entry. Returns `204` with no body. Same ownership rules as GET. |

`mood` must be one of: `great`, `good`, `okay`, `low`, `bad`.

**Example: list response**
```json
{
  "mood_entries": [
    {
      "id": 12,
      "user_id": 1,
      "mood": "good",
      "note": "Productive day",
      "created_at": "2026-08-01T21:03:15",
      "updated_at": "2026-08-01T21:03:15"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total_items": 13,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

## Error format

Every error response is `{"errors": [...]}`, always a flat array of
strings (this specific shape is required by the frontend, which calls
`err.errors.map(...)` directly):

```json
{ "errors": ["username: Username must be between 3 and 20 characters."] }
```

| Status | Meaning |
|--------|---------|
| 400 | Validation error (bad/missing fields) |
| 401 | Missing, invalid, or expired token; or wrong login credentials |
| 403 | The record exists, but doesn't belong to you |
| 404 | The record doesn't exist |
| 409 | Username already taken (signup) |

## Testing with Postman

1. `POST /signup` → copy the returned `token`.
2. Set `Authorization: Bearer <token>` (Postman: collection-level Bearer
   Token auth, with each request set to "Inherit auth from parent," is
   the least repetitive way to do this).
3. Exercise `/mood_entries` CRUD as that user.
4. Sign up a second user and confirm `GET/PATCH/DELETE` on the first
   user's entries returns `403` — this is the check that proves users
   can't touch each other's data.

## Known gotchas

- **`AttributeError: module 'ast' has no attribute 'Str'`** — you're
  running Python 3.14+. Werkzeug 2.2.2 (pinned by this assignment)
  doesn't support it. See the "Installing Python 3.11" and the
  `Pipfile` warning box in the Installation section above.
- **`error: externally-managed-environment` when running
  `pip install --user pipenv` on Linux** — recent Debian/Ubuntu blocks
  `pip` from touching the system Python directly (PEP 668). Use `pipx`
  instead (see Installation section above), or add
  `--break-system-packages` to the pip command.
- **SQLite file location** — Flask-SQLAlchemy puts `app.db` inside an
  `instance/` folder, not the project root, even though the config just
  says `sqlite:///app.db`. This is normal.
- **`npm start` fails with `'PORT' is not recognized`** — on
  Windows/Git Bash, `npm run start` executes through `cmd.exe`, which
  doesn't understand `VAR=value command` syntax. Run
  `PORT=4000 npx react-scripts start` directly instead.

  # Author
  -Samwel Macharia