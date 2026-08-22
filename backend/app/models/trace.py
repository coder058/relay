"""Trace, Approval, and Playback Models."""

from typing import Any
from pydantic import BaseModel, Field


class TraceRecord(BaseModel):
    """Append-only trace record stored in SQLite."""

    id: str
    timestamp: str  # ISO-8601 UTC
    session_id: str
    request_id: str | int | None = None
    method: str
    tool_name: str | None = None
    # Compatibility field: this is sanitized before persistence, never raw secrets.
    raw_arguments: dict[str, Any] | None = None
    redacted_arguments: dict[str, Any] | None = None
    policy_decision: str  # "allow" | "deny" | "require_approval" | "approved" | "denied_by_operator"
    matched_rule_id: str | None = None
    policy_reason: str | None = None
    risk_level: str | None = None
    approval_id: str | None = None
    approval_status: str | None = None  # "none" | "pending" | "approved" | "denied" | "expired"
    # Compatibility field: this is sanitized before persistence, never raw secrets.
    raw_result: Any | None = None
    redacted_result: Any | None = None
    error: str | None = None
    duration_ms: float = 0.0
    simulated_tokens: int | None = None
    simulated_cost_usd: float | None = None
    is_synthetic: bool = False


class ApprovalRecord(BaseModel):
    """Record of an approval lifecycle state."""

    id: str
    trace_id: str
    session_id: str
    tool_name: str
    arguments_hash: str
    token: str
    status: str = "pending"  # "pending" | "approved" | "denied" | "expired" | "consumed"
    risk_level: str = "medium"
    reason: str = ""
    raw_arguments: dict[str, Any] | None = None
    redacted_arguments: dict[str, Any] | None = None
    created_at: str
    expires_at: str
    decided_at: str | None = None
    decided_by: str | None = None


class ApprovalDecisionRequest(BaseModel):
    """Payload sent by human operator to approve or deny a pending request."""

    token: str
    decision: str = Field(..., pattern=r"^(approve|deny)$")
    actor: str = "human_operator"
    reason: str | None = None


class TraceFilter(BaseModel):
    """Filter parameters for trace queries."""

    session_id: str | None = None
    tool_name: str | None = None
    policy_decision: str | None = None
    risk_level: str | None = None
    limit: int = 50
    offset: int = 0


class PlaybackRequest(BaseModel):
    """Request to replay a safe captured trace."""

    trace_id: str
    override_arguments: dict[str, Any] | None = None


class PlaybackResult(BaseModel):
    """Result of replaying a captured trace."""

    original_trace_id: str
    replayed_at: str
    tool_name: str
    arguments: dict[str, Any]
    original_decision: str
    playback_decision: str
    decision_matches: bool
    playback_duration_ms: float
    original_duration_ms: float
    output: Any | None = None
    error: str | None = None
