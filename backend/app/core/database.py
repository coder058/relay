"""SQLite Database Layer for Relay MCP Safety Lab.

Manages tables for append-only traces, approvals, session spends, and demo fixtures.
"""

from pathlib import Path
import aiosqlite
from app.config import settings

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT,
    method TEXT NOT NULL,
    tool_name TEXT,
    raw_arguments_json TEXT,
    redacted_arguments_json TEXT,
    policy_decision TEXT NOT NULL,
    matched_rule_id TEXT,
    policy_reason TEXT,
    risk_level TEXT,
    approval_id TEXT,
    approval_status TEXT,
    raw_result_json TEXT,
    redacted_result_json TEXT,
    error TEXT,
    duration_ms REAL DEFAULT 0.0,
    simulated_tokens INTEGER,
    simulated_cost_usd REAL,
    is_synthetic INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_traces_session ON traces (session_id);
CREATE INDEX IF NOT EXISTS idx_traces_tool ON traces (tool_name);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces (timestamp DESC);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments_hash TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    reason TEXT,
    redacted_arguments_json TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    decided_at TEXT,
    decided_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_approvals_token ON approvals (token);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals (status);

CREATE TABLE IF NOT EXISTS session_spends (
    session_id TEXT PRIMARY KEY,
    total_spend_usd REAL DEFAULT 0.0,
    total_calls INTEGER DEFAULT 0,
    last_activity TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS demo_fixture_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    account_balance REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Database:
    """Async SQLite Database Wrapper."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path

    async def init_db(self) -> None:
        """Create database directory and initialize schema tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(CREATE_TABLES_SQL)
            await db.commit()

    async def get_connection(self) -> aiosqlite.Connection:
        """Get an async connection configured with foreign keys and dict row factory."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn


# Singleton database instance
db = Database()
