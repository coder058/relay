"""Pytest configuration and shared test fixtures."""

import os
import tempfile
import pytest_asyncio
from app.core.database import Database
from app.services.demo_fixtures import reset_fixtures


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Create a pristine temporary SQLite database for each test run."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = tmp.name

    test_db = Database(db_path=temp_db_path)
    monkeypatch.setattr("app.core.database.db", test_db)
    monkeypatch.setattr("app.services.demo_fixtures.db", test_db)
    monkeypatch.setattr("app.services.trace_service.db", test_db)
    monkeypatch.setattr("app.core.approval_manager.db", test_db)
    monkeypatch.setattr("app.core.policy_engine.db", test_db)

    await test_db.init_db()
    await reset_fixtures()

    yield test_db

    try:
        os.remove(temp_db_path)
    except OSError:
        pass
