import os

os.environ["SQLITE_DB_PATH"] = ":memory:" # Use memory for tests, wait actually db config uses settings.sqlite_db_path, let's just let it create relay.db or test.db

import app.config
app.config.settings.sqlite_db_path = "test_relay.db"
