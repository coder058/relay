"""Tests for Policy Engine rule evaluation, predicates, and budget limits."""

import pytest
from app.core.policy_engine import PolicyEngine
from app.models.policy import (
    ArgumentPredicate,
    PolicyAction,
    PolicyConfig,
    PolicyRule,
    PredicateOperator,
    RiskLevel,
)


@pytest.mark.asyncio
async def test_policy_allows_safe_read():
    engine = PolicyEngine()
    result = await engine.evaluate(
        session_id="test-session",
        tool_name="read_record",
        arguments={"customer_id": "CUST-1001"},
    )
    assert result.action == PolicyAction.ALLOW
    assert result.approval_required is False
    assert result.risk_level == RiskLevel.LOW


@pytest.mark.asyncio
async def test_policy_requires_approval_for_delete():
    engine = PolicyEngine()
    result = await engine.evaluate(
        session_id="test-session",
        tool_name="delete_record",
        arguments={"customer_id": "CUST-1001"},
    )
    assert result.action == PolicyAction.REQUIRE_APPROVAL
    assert result.approval_required is True
    assert result.risk_level == RiskLevel.HIGH


@pytest.mark.asyncio
async def test_policy_blocks_prohibited_shell():
    engine = PolicyEngine()
    result = await engine.evaluate(
        session_id="test-session",
        tool_name="system_shell_exec",
        arguments={"command": "whoami"},
    )
    assert result.action == PolicyAction.DENY
    assert result.risk_level == RiskLevel.CRITICAL


@pytest.mark.asyncio
async def test_argument_predicate_greater_than():
    # Rule: require approval if balance update > 5000
    rule = PolicyRule(
        id="rule-high-value-gate",
        name="High Value Update Gate",
        tool_pattern="update_balance",
        action=PolicyAction.REQUIRE_APPROVAL,
        risk_level=RiskLevel.HIGH,
        argument_predicates=[
            ArgumentPredicate(
                field="amount",
                operator=PredicateOperator.GREATER_THAN,
                value=5000,
            )
        ],
    )
    config = PolicyConfig(
        session_spend_limit_usd=10.0,
        default_action=PolicyAction.ALLOW,
        rules=[rule],
    )
    engine = PolicyEngine(config=config)

    # Low value -> fallback allow
    res_low = await engine.evaluate("s1", "update_balance", {"amount": 100})
    assert res_low.action == PolicyAction.ALLOW

    # High value -> triggered require_approval
    res_high = await engine.evaluate("s1", "update_balance", {"amount": 8000})
    assert res_high.action == PolicyAction.REQUIRE_APPROVAL
    assert res_high.matched_rule_id == "rule-high-value-gate"


@pytest.mark.asyncio
async def test_session_budget_ceiling_enforcement():
    config = PolicyConfig(
        session_spend_limit_usd=0.05,  # 5 cents
        default_action=PolicyAction.ALLOW,
        rules=[],
    )
    engine = PolicyEngine(config=config)
    session_id = "budget-test-session"

    # First call within budget
    res1 = await engine.evaluate(session_id, "read_record", {}, estimated_cost_usd=0.02)
    assert res1.action == PolicyAction.ALLOW
    await engine.record_session_spend(session_id, cost_usd=0.04)

    # Second call exceeds ceiling (0.04 + 0.02 > 0.05)
    res2 = await engine.evaluate(session_id, "read_record", {}, estimated_cost_usd=0.02)
    assert res2.action == PolicyAction.DENY
    assert "Session spend limit" in res2.reason
