"""Safe Local Demo Fixtures Service.

Provides an isolated, in-memory / SQLite fixture of records so the demo can execute
safe operations and risky operations (e.g. delete_record) without external side effects,
and can be cleanly reset at any time.
"""

from datetime import datetime, timezone
from typing import Any
from app.core.database import db

# Initial baseline demo records
INITIAL_RECORDS = [
    {
        "customer_id": "CUST-1001",
        "name": "Alice Montgomery",
        "email": "alice.montgomery@example.com",
        "account_balance": 1420.50,
        "status": "active",
    },
    {
        "customer_id": "CUST-1002",
        "name": "Bob Vance",
        "email": "bob.vance@example.com",
        "account_balance": 310.00,
        "status": "active",
    },
    {
        "customer_id": "CUST-1003",
        "name": "Charlie Chaplin",
        "email": "charlie.c@example.com",
        "account_balance": 8750.25,
        "status": "premium",
    },
    {
        "customer_id": "CUST-1004",
        "name": "Dana Scully",
        "email": "scully@example.com",
        "account_balance": 450.00,
        "status": "flagged_review",
    },
]


async def seed_fixtures_if_empty() -> None:
    """Populate default fixture records if the table is currently empty."""
    conn = await db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM demo_fixture_records")
            row = await cur.fetchone()
            count = row[0] if row else 0

            if count == 0:
                now_iso = datetime.now(timezone.utc).isoformat()
                for rec in INITIAL_RECORDS:
                    await cur.execute(
                        """
                        INSERT INTO demo_fixture_records (customer_id, name, email, account_balance, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (rec["customer_id"], rec["name"], rec["email"], rec["account_balance"], rec["status"], now_iso),
                    )
                await conn.commit()
    finally:
        await conn.close()


async def reset_fixtures() -> list[dict[str, Any]]:
    """Wipe and re-seed all demo fixture records to their pristine initial state."""
    conn = await db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM demo_fixture_records")
            now_iso = datetime.now(timezone.utc).isoformat()
            for rec in INITIAL_RECORDS:
                await cur.execute(
                    """
                    INSERT INTO demo_fixture_records (customer_id, name, email, account_balance, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (rec["customer_id"], rec["name"], rec["email"], rec["account_balance"], rec["status"], now_iso),
                )
            await conn.commit()
    finally:
        await conn.close()
    return await list_fixture_records()


async def list_fixture_records() -> list[dict[str, Any]]:
    """List all records in the safe local fixture database."""
    conn = await db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT customer_id, name, email, account_balance, status, created_at FROM demo_fixture_records ORDER BY customer_id ASC")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        await conn.close()


async def get_fixture_record(customer_id: str) -> dict[str, Any] | None:
    """Retrieve a single fixture record by customer_id."""
    conn = await db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT customer_id, name, email, account_balance, status, created_at FROM demo_fixture_records WHERE customer_id = ?",
                (customer_id,),
            )
            row = await cur.fetchone()
            return dict(row) if row else None
    finally:
        await conn.close()


async def create_fixture_record(customer_id: str, name: str, email: str, account_balance: float = 0.0, status: str = "active") -> dict[str, Any]:
    """Create a new fixture record safely."""
    conn = await db.get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO demo_fixture_records (customer_id, name, email, account_balance, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (customer_id, name, email, account_balance, status, now_iso),
            )
            await conn.commit()
        return {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "account_balance": account_balance,
            "status": status,
            "created_at": now_iso,
        }
    finally:
        await conn.close()


async def delete_fixture_record(customer_id: str) -> bool:
    """Delete a fixture record (used for demonstrating approval gate for destructive actions)."""
    conn = await db.get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM demo_fixture_records WHERE customer_id = ?", (customer_id,))
            deleted = cur.rowcount > 0
            await conn.commit()
            return deleted
    finally:
        await conn.close()
