"""Approval Manager for Relay MCP Safety Lab.

Generates single-use approval tokens bound to trace_id, session_id, tool_name,
and canonical arguments hash, enforcing time-to-live expiry and single-use consumption.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Any
from app.config import settings
from app.core.database import db
from app.core.redaction import redact_data
from app.models.trace import ApprovalRecord


def compute_arguments_hash(trace_id: str, session_id: str, tool_name: str, arguments: dict[str, Any] | None) -> str:
    """Compute deterministic SHA-256 hash over canonical request parameters.

    Binds the approval specifically to this exact invocation to prevent replay attacks.
    """
    canonical_args = json.dumps(arguments or {}, sort_keys=True, separators=(",", ":"))
    payload = f"{trace_id}:{session_id}:{tool_name}:{canonical_args}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ApprovalManager:
    """Manages creation, verification, decisioning, and consumption of approval tokens."""

    @staticmethod
    async def create_approval(
        trace_id: str,
        session_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None,
        risk_level: str = "medium",
        reason: str = "",
        ttl_seconds: float | None = None,
    ) -> ApprovalRecord:
        """Create a new pending approval record with a cryptographically secure token."""
        ttl = ttl_seconds or settings.approval_token_ttl_seconds
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)

        arguments_hash = compute_arguments_hash(trace_id, session_id, tool_name, arguments)
        token = f"appr_{secrets.token_urlsafe(24)}"
        approval_id = f"appr_id_{secrets.token_hex(8)}"

        redacted_args = redact_data(arguments or {})

        record = ApprovalRecord(
            id=approval_id,
            trace_id=trace_id,
            session_id=session_id,
            tool_name=tool_name,
            arguments_hash=arguments_hash,
            token=token,
            status="pending",
            risk_level=risk_level,
            reason=reason,
            raw_arguments=arguments,
            redacted_arguments=redacted_args,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )

        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO approvals (
                        id, trace_id, session_id, tool_name, arguments_hash, token,
                        status, risk_level, reason, redacted_arguments_json, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.trace_id,
                        record.session_id,
                        record.tool_name,
                        record.arguments_hash,
                        record.token,
                        record.status,
                        record.risk_level,
                        record.reason,
                        json.dumps(record.redacted_arguments),
                        record.created_at,
                        record.expires_at,
                    ),
                )
                await conn.commit()
        finally:
            await conn.close()

        return record

    @staticmethod
    async def list_pending_approvals() -> list[dict[str, Any]]:
        """List all currently active pending approvals (auto-expiring stale ones)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                # Mark expired items
                await cur.execute(
                    "UPDATE approvals SET status = 'expired' WHERE status = 'pending' AND expires_at < ?",
                    (now_iso,),
                )
                await conn.commit()

                await cur.execute(
                    """
                    SELECT id, trace_id, session_id, tool_name, arguments_hash, token,
                           status, risk_level, reason, redacted_arguments_json, created_at, expires_at,
                           decided_at, decided_by
                    FROM approvals
                    ORDER BY created_at DESC
                    """
                )
                rows = await cur.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    if d.get("redacted_arguments_json"):
                        try:
                            d["redacted_arguments"] = json.loads(d["redacted_arguments_json"])
                        except Exception:
                            d["redacted_arguments"] = {}
                    results.append(d)
                return results
        finally:
            await conn.close()

    @staticmethod
    async def get_approval_by_token(token: str) -> dict[str, Any] | None:
        """Fetch approval record by token and evaluate expiration."""
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM approvals WHERE token = ?", (token,))
                row = await cur.fetchone()
                if not row:
                    return None
                data = dict(row)
                if data["status"] == "pending":
                    now = datetime.now(timezone.utc)
                    expires = datetime.fromisoformat(data["expires_at"])
                    if now > expires:
                        data["status"] = "expired"
                        await cur.execute(
                            "UPDATE approvals SET status = 'expired' WHERE token = ?", (token,)
                        )
                        await conn.commit()
                if data.get("redacted_arguments_json"):
                    try:
                        data["redacted_arguments"] = json.loads(data["redacted_arguments_json"])
                    except Exception:
                        data["redacted_arguments"] = {}
                return data
        finally:
            await conn.close()

    @staticmethod
    async def decide_approval(
        token: str,
        decision: str,  # "approve" | "deny"
        actor: str = "human_operator",
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Operator action to approve or deny a pending approval request."""
        approval = await ApprovalManager.get_approval_by_token(token)
        if not approval:
            raise ValueError(f"Approval token '{token}' not found.")

        if approval["status"] == "expired":
            raise ValueError("Approval token has expired.")

        if approval["status"] != "pending":
            raise ValueError(f"Approval token is already in status '{approval['status']}'.")

        new_status = "approved" if decision == "approve" else "denied"
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE approvals
                    SET status = ?, decided_at = ?, decided_by = ?, reason = COALESCE(?, reason)
                    WHERE token = ?
                    """,
                    (new_status, now_iso, actor, reason, token),
                )
                await conn.commit()
        finally:
            await conn.close()

        approval["status"] = new_status
        approval["decided_at"] = now_iso
        approval["decided_by"] = actor
        if reason:
            approval["reason"] = reason
        return approval

    @staticmethod
    async def consume_approval_token(
        token: str,
        trace_id: str,
        session_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None,
    ) -> bool:
        """Validate that the token was approved, bound to these exact parameters, and consume it.

        Returns True if successfully consumed, False otherwise.
        """
        approval = await ApprovalManager.get_approval_by_token(token)
        if not approval:
            return False

        if approval["status"] != "approved":
            return False

        expected_hash = compute_arguments_hash(trace_id, session_id, tool_name, arguments)
        if approval["arguments_hash"] != expected_hash:
            return False

        # Mark as consumed immediately so it cannot be used a second time
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE approvals SET status = 'consumed' WHERE token = ? AND status = 'approved'",
                    (token,),
                )
                await conn.commit()
                return cur.rowcount > 0
        finally:
            await conn.close()
