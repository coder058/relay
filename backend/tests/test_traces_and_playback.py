"""Tests for Append-Only Trace Storage and Deterministic Playback."""

import pytest
from app.models.trace import TraceFilter
from app.services.trace_service import TraceService


@pytest.mark.asyncio
async def test_trace_storage_and_query():
    session_id = "test-trace-sess-1"

    # Record two traces
    t1 = await TraceService.record_trace(
        session_id=session_id,
        method="tools/call",
        tool_name="read_record",
        raw_arguments={"customer_id": "CUST-1001"},
        policy_decision="allow",
        matched_rule_id="rule-allow-safe-reads",
        policy_reason="Allowed read",
        risk_level="low",
        approval_id=None,
        approval_status=None,
        raw_result={"status": "ok"},
        error=None,
        duration_ms=1.5,
    )

    await TraceService.record_trace(
        session_id=session_id,
        method="tools/call",
        tool_name="delete_record",
        raw_arguments={"customer_id": "CUST-1004"},
        policy_decision="require_approval",
        matched_rule_id="rule-approval-delete",
        policy_reason="Approval required for delete",
        risk_level="high",
        approval_id="appr_123",
        approval_status="pending",
        raw_result=None,
        error=None,
        duration_ms=0.8,
    )

    # Query traces
    results = await TraceService.list_traces(TraceFilter(session_id=session_id))
    assert results["total"] == 2
    assert len(results["traces"]) == 2

    # Query with decision filter
    filtered = await TraceService.list_traces(TraceFilter(session_id=session_id, policy_decision="allow"))
    assert filtered["total"] == 1
    assert filtered["traces"][0]["id"] == t1.id


@pytest.mark.asyncio
async def test_replay_trace_determinism():
    session_id = "test-replay-sess"
    trace = await TraceService.record_trace(
        session_id=session_id,
        method="tools/call",
        tool_name="read_record",
        raw_arguments={"customer_id": "CUST-1001"},
        policy_decision="allow",
        matched_rule_id="rule-allow-safe-reads",
        policy_reason="Allowed read",
        risk_level="low",
        approval_id=None,
        approval_status=None,
        raw_result={"content": [{"text": "sample"}]},
        error=None,
        duration_ms=2.0,
    )

    playback = await TraceService.replay_trace(trace.id)
    assert playback.original_trace_id == trace.id
    assert playback.decision_matches is True
    assert playback.playback_decision == "allow"
    assert playback.playback_duration_ms >= 0.0


@pytest.mark.asyncio
async def test_trace_persistence_never_keeps_original_secret_values():
    trace = await TraceService.record_trace(
        session_id="test-redaction-persistence",
        method="tools/call",
        tool_name="echo",
        raw_arguments={
            "api_key": "sk-1234567890abcdef1234567890abcdef",
            "email": "operator@example.com",
        },
        policy_decision="allow",
        matched_rule_id="rule-allow-safe-reads",
        policy_reason="Safe test call",
        risk_level="low",
        approval_id=None,
        approval_status="none",
        raw_result={"token": "Bearer test-secret-token"},
        error=None,
        duration_ms=1.0,
    )

    stored = await TraceService.get_trace(trace.id)
    assert stored is not None
    serialized = str(stored)
    assert "sk-1234567890abcdef1234567890abcdef" not in serialized
    assert "operator@example.com" not in serialized
    assert "Bearer test-secret-token" not in serialized
    assert "[REDACTED_SECRET]" in serialized or "[REDACTED_BEARER_TOKEN]" in serialized
