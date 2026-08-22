import pytest
from app.core.policy_engine import policy_engine
from app.models.policy import PolicyAction, RiskLevel

@pytest.mark.asyncio
async def test_policy_allow_read():
    res = await policy_engine.evaluate("sess_1", "read_record", {"customer_id": "CUST-1001"})
    assert res.action == PolicyAction.ALLOW
    assert res.risk_level == RiskLevel.LOW

@pytest.mark.asyncio
async def test_policy_deny_exec():
    res = await policy_engine.evaluate("sess_1", "shell_exec", {"cmd": "rm -rf /"})
    assert res.action == PolicyAction.DENY
    assert res.risk_level == RiskLevel.CRITICAL

@pytest.mark.asyncio
async def test_policy_require_approval_delete():
    res = await policy_engine.evaluate("sess_1", "delete_record", {"customer_id": "CUST-1001"})
    assert res.action == PolicyAction.REQUIRE_APPROVAL
    assert res.risk_level == RiskLevel.HIGH
