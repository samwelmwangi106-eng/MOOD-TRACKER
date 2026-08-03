
# Populates the database with demo data for manual testing (Postman, the
# React client, etc). Safe to re-run any time -- it clears out existing
# rows first rather than piling up duplicates on every run.
#
# Note: this does NOT create tables. Tables are managed by Flask-Migrate
# (`flask db upgrade`) -- this script only inserts rows into tables that
# already exist. Run the migration first if you haven't.
#
# Usage:
#   FLASK_APP=app.py pipenv run flask db upgrade   # if not already done
#   pipenv run python seed.py

import random
from faker import Faker

from config import app, db
from models import User, MoodEntry
from models.mood_entry import MOOD_CHOICES

fake = Faker()
Faker.seed(42)  # reproducible data -- same run every time, easier to debug against

# A couple of accounts with known, memorable credentials, so you always
# have something to log in with immediately (Postman, the frontend, etc)
# without having to dig through generated data first.
DEMO_ACCOUNTS = [
    {"username": "alice", "password": "password123"},
    {"username": "bob", "password": "password123"},
]

NUM_RANDOM_USERS = 3           # additional Faker-generated users, for bulk/pagination testing
MIN_ENTRIES_PER_USER = 8       # kept >10 for at least one user so pagination is easy to see (default per_page=10)
MAX_ENTRIES_PER_USER = 16


def clear_existing_data():
    """Delete rows (not tables) so this script can be re-run safely.

    Order matters: MoodEntry rows reference users.id via a foreign key,
    so they have to go first, or the database will reject deleting a
    user that still has entries pointing at it.
    """
    MoodEntry.query.delete()
    User.query.delete()
    db.session.commit()


def create_user(username, password):
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    return user


def create_mood_entries_for(user):
    entry_count = random.randint(MIN_ENTRIES_PER_USER, MAX_ENTRIES_PER_USER)
    for _ in range(entry_count):
        entry = MoodEntry(
            user_id=user.id,
            mood=random.choice(MOOD_CHOICES),
            # Roughly half the entries have a note, half don't -- mirrors
            # how a real user wouldn't always bother writing something.
            note=fake.sentence() if random.random() < 0.5 else None,
        )
        db.session.add(entry)
    return entry_count


def seed():
    with app.app_context():
        clear_existing_data()

        created_users = []

        # Known demo accounts first
        for account in DEMO_ACCOUNTS:
            user = create_user(account["username"], account["password"])
            created_users.append(user)

        # Extra random users for volume
        for _ in range(NUM_RANDOM_USERS):
            username = fake.unique.user_name()
            user = create_user(username, "password123")
            created_users.append(user)

        # Flush (not commit) so each user gets a real id from the database
        # before we use it as a foreign key on their mood entries below.
        db.session.flush()

        total_entries = 0
        for user in created_users:
            total_entries += create_mood_entries_for(user)

        db.session.commit()

        print(f"Seeded {len(created_users)} users and {total_entries} mood entries.\n")
        print("Demo login credentials:")
        for account in DEMO_ACCOUNTS:
            print(f"  username: {account['username']}   password: {account['password']}")


if __name__ == "__main__":
    seed()