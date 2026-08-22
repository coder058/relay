"""Tests for Human-in-the-Loop Approval Workflow, Single-Use Token Binding, and Expiry."""

import asyncio
import json
import pytest
from app.core.approval_manager import ApprovalManager
from app.mcp.proxy import proxy


@pytest.mark.asyncio
async def test_complete_approval_lifecycle():
    session_id = "test-approval-session"
    delete_payload = {
        "jsonrpc": "2.0",
        "id": "del_1",
        "method": "tools/call",
        "params": {"name": "delete_record", "arguments": {"customer_id": "CUST-1002"}},
    }

    # 1. First invocation triggers approval required
    res1 = await proxy.process_request(delete_payload, session_id=session_id)
    assert res1.get("error") is not None
    assert res1["error"]["code"] == -32001
    appr_data = res1["error"]["data"]
    token = appr_data["approval_token"]
    assert token.startswith("appr_")

    # 2. Operator approves ticket
    decision = await ApprovalManager.decide_approval(
        token=token,
        decision="approve",
        actor="test_admin",
        reason="Verified test deletion",
    )
    assert decision["status"] == "approved"

    # 3. Resume invocation with token
    res2 = await proxy.process_request(
        {
            "jsonrpc": "2.0",
            "id": "del_2",
            "method": "tools/call",
            "params": {
                "name": "delete_record",
                "arguments": {"customer_id": "CUST-1002"},
                "_approval_token": token,
            },
        },
        session_id=session_id,
    )
    assert res2.get("error") is None
    assert res2.get("result") is not None
    assert "deleted" in json.dumps(res2["result"]) if isinstance(res2["result"], dict) else True

    # 4. Attempt to REUSE the single-use token -> Must fail!
    res3 = await proxy.process_request(
        {
            "jsonrpc": "2.0",
            "id": "del_3",
            "method": "tools/call",
            "params": {
                "name": "delete_record",
                "arguments": {"customer_id": "CUST-1002"},
                "_approval_token": token,
            },
        },
        session_id=session_id,
    )
    assert res3.get("error") is not None
    assert res3["error"]["code"] == -32001
    assert "consumed" in res3["error"]["message"].lower() or "invalid" in res3["error"]["message"].lower()


@pytest.mark.asyncio
async def test_tampered_arguments_fail_hash_binding():
    session_id = "test-tamper-session"
    res1 = await proxy.process_request(
        {
            "jsonrpc": "2.0",
            "id": "req_1",
            "method": "tools/call",
            "params": {"name": "delete_record", "arguments": {"customer_id": "CUST-1001"}},
        },
        session_id=session_id,
    )
    token = res1["error"]["data"]["approval_token"]
    await ApprovalManager.decide_approval(token, "approve")

    # Attempt to consume token with DIFFERENT arguments (CUST-1003 instead of CUST-1001)
    res2 = await proxy.process_request(
        {
            "jsonrpc": "2.0",
            "id": "req_2",
            "method": "tools/call",
            "params": {
                "name": "delete_record",
                "arguments": {"customer_id": "CUST-1003"},
                "_approval_token": token,
            },
        },
        session_id=session_id,
    )
    assert res2.get("error") is not None
    assert res2["error"]["code"] == -32001


@pytest.mark.asyncio
async def test_approval_token_expiry():
    # Create an approval with a 0.05s TTL
    record = await ApprovalManager.create_approval(
        trace_id="trc_expire_test",
        session_id="sess_expire",
        tool_name="delete_record",
        arguments={"customer_id": "CUST-1001"},
        ttl_seconds=0.05,
    )

    await asyncio.sleep(0.08)

    # Attempting to fetch or decide on expired token
    with pytest.raises(ValueError, match="expired"):
        await ApprovalManager.decide_approval(record.token, "approve")
