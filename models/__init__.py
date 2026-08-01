# models/__init__.py
#
# Flask-Migrate detects tables by looking at everything registered on
# db.metadata. That only happens if each model class has actually been
# imported somewhere. Rather than remembering to import User and
# MoodEntry individually all over the app, we import them once here --
# so `from models import User, MoodEntry` (or even just `import models`)
# is enough to make sure both tables are known to Flask-Migrate.

from models.user import User
from models.mood_entry import MoodEntry