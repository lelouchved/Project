import os
import shutil

TEST_DB_PATH = "./test_temp_tracker.db"

# Copy live database to temporary isolated test database before any backend imports
if os.path.exists("./club_tracker.db"):
    shutil.copy("./club_tracker.db", TEST_DB_PATH)

# Set environment variable so backend.database initializes directly with the isolated test DB
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest
import backend.database as db_module

@pytest.fixture(scope="session", autouse=True)
def cleanup_isolated_test_database():
    """
    Ensures tests run in a completely isolated database copy.
    Tests will NEVER add, alter, or pollute data in the real club_tracker.db.
    """
    yield

    db_module.engine.dispose()
    for f in [TEST_DB_PATH, f"{TEST_DB_PATH}-wal", f"{TEST_DB_PATH}-shm"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
