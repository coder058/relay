"""Policy Engine for Relay MCP Safety Lab.

Evaluates MCP tool execution requests against configured rules, argument predicates,
and session spend ceilings with clear explanations and SOURCE/GUESS/PLACEHOLDER documentation.
"""

from datetime import datetime, timezone
import fnmatch
import re
from typing import Any
from app.config import settings
from app.core.database import db
from app.models.policy import (
    ArgumentPredicate,
    PolicyAction,
    PolicyConfig,
    PolicyEvaluationResult,
    PolicyRule,
    PredicateOperator,
    RiskLevel,
)

# Default baseline policy rules for safe local execution
# GUESS: standard demo configuration separating read-only, benign writes, and destructive operations
DEFAULT_POLICY_RULES = [
    PolicyRule(
        id="rule-allow-safe-reads",
        name="Allow Safe Read Operations",
        tool_pattern="read_*",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.LOW,
        description="Allow read-only tool calls without interruption",
    ),
    PolicyRule(
        id="rule-allow-list-tools",
        name="Allow List Tools",
        tool_pattern="*list*",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.LOW,
        description="Allow safe discovery and list tools",
    ),
    PolicyRule(
        id="rule-allow-echo-tools",
        name="Allow Echo Tools",
        tool_pattern="*echo*",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.LOW,
        description="Allow deterministic echo tools in the local demo",
    ),
    PolicyRule(
        id="rule-allow-metrics-tools",
        name="Allow Metrics Tools",
        tool_pattern="*metrics*",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.LOW,
        description="Allow safe local telemetry tools",
    ),
    PolicyRule(
        id="rule-allow-create",
        name="Allow Record Creation",
        tool_pattern="create_record",
        action=PolicyAction.ALLOW,
        risk_level=RiskLevel.LOW,
        description="Allow non-destructive record additions to demo fixture",
    ),
    PolicyRule(
        id="rule-approval-delete",
        name="Require Operator Approval for Record Deletion",
        tool_pattern="delete_*",
        action=PolicyAction.REQUIRE_APPROVAL,
        risk_level=RiskLevel.HIGH,
        description="Require explicit human operator approval before executing destructive delete operations",
    ),
    PolicyRule(
        id="rule-deny-exec-tools",
        name="Block Arbitrary System Execution",
        tool_pattern="*exec*",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Strictly block any attempts at arbitrary command execution",
    ),
    PolicyRule(
        id="rule-deny-shell-tools",
        name="Block Shell Tools",
        tool_pattern="*shell*",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Strictly block shell tools in the local proxy",
    ),
    PolicyRule(
        id="rule-deny-interpreter-tools",
        name="Block Interpreter Tools",
        tool_pattern="*bash*",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Strictly block interpreter tools in the local proxy",
    ),
    PolicyRule(
        id="rule-deny-eval-tools",
        name="Block Evaluation Tools",
        tool_pattern="*eval*",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Strictly block dynamic evaluation tools",
    ),
    PolicyRule(
        id="rule-deny-command-tools",
        name="Block Command Tools",
        tool_pattern="*cmd*",
        action=PolicyAction.DENY,
        risk_level=RiskLevel.CRITICAL,
        description="Strictly block command tools in the local proxy",
    ),
]


class PolicyEngine:
    """Evaluates requests against security policies, predicates, and session budgets."""

    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig(
            # PLACEHOLDER: conservative session spend limit ($1.00 USD)
            session_spend_limit_usd=settings.default_session_spend_limit_usd,
            # GUESS: deny unrecognized tools by default under zero-trust principles
            default_action=PolicyAction.DENY,
            rules=DEFAULT_POLICY_RULES,
        )

    def set_config(self, config: PolicyConfig) -> None:
        """Update active policy configuration."""
        self.config = config

    def get_config(self) -> PolicyConfig:
        """Get current policy configuration."""
        return self.config

    async def get_session_spend(self, session_id: str) -> float:
        """Retrieve cumulative spend for a session from SQLite."""
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT total_spend_usd FROM session_spends WHERE session_id = ?",
                    (session_id,),
                )
                row = await cur.fetchone()
                return float(row[0]) if row else 0.0
        finally:
            await conn.close()

    async def record_session_spend(self, session_id: str, cost_usd: float) -> None:
        """Increment cumulative session spend."""
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO session_spends (session_id, total_spend_usd, total_calls, last_activity)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        total_spend_usd = total_spend_usd + excluded.total_spend_usd,
                        total_calls = total_calls + 1,
                        last_activity = excluded.last_activity
                    """,
                    (session_id, cost_usd, now_iso),
                )
                await conn.commit()
        finally:
            await conn.close()

    def _evaluate_predicate(self, predicate: ArgumentPredicate, arguments: dict[str, Any]) -> bool:
        """Evaluate a single argument predicate against tool arguments."""
        val = arguments.get(predicate.field)
        op = predicate.operator
        target = predicate.value

        if op == PredicateOperator.EXISTS:
            return predicate.field in arguments

        if val is None:
            return False

        if op == PredicateOperator.EQUALS:
            return str(val) == str(target)
        elif op == PredicateOperator.NOT_EQUALS:
            return str(val) != str(target)
        elif op == PredicateOperator.CONTAINS:
            return str(target) in str(val)
        elif op == PredicateOperator.NOT_CONTAINS:
            return str(target) not in str(val)
        elif op == PredicateOperator.REGEX_MATCH:
            return bool(re.search(str(target), str(val)))
        elif op == PredicateOperator.IN_LIST:
            if isinstance(target, list):
                return val in target or str(val) in [str(x) for x in target]
            return False
        elif op == PredicateOperator.GREATER_THAN:
            try:
                return float(val) > float(target)
            except (ValueError, TypeError):
                return False
        elif op == PredicateOperator.LESS_THAN:
            try:
                return float(val) < float(target)
            except (ValueError, TypeError):
                return False

        return False

    async def evaluate(
        self,
        session_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        estimated_cost_usd: float = 0.0,
    ) -> PolicyEvaluationResult:
        """Evaluate a tool invocation against budget, rules, and predicates."""
        args = arguments or {}

        # 1. Budget check
        current_spend = await self.get_session_spend(session_id)
        if current_spend + estimated_cost_usd > self.config.session_spend_limit_usd:
            return PolicyEvaluationResult(
                action=PolicyAction.DENY,
                reason=(
                    f"Session spend limit of ${self.config.session_spend_limit_usd:.2f} exceeded "
                    f"(current: ${current_spend:.4f}, requested: ${estimated_cost_usd:.4f})"
                ),
                risk_level=RiskLevel.HIGH,
                approval_required=False,
            )

        # 2. Rule evaluation (in order)
        for rule in self.config.rules:
            if not rule.enabled:
                continue

            # Tool pattern match (glob support, e.g. "delete_*")
            matched_pattern = fnmatch.fnmatch(tool_name.lower(), rule.tool_pattern.lower())
            if not matched_pattern:
                continue

            # Predicates match (all predicates must match if present)
            predicates_pass = True
            for predicate in rule.argument_predicates:
                if not self._evaluate_predicate(predicate, args):
                    predicates_pass = False
                    break

            if not predicates_pass:
                continue

            # Rule matched!
            approval_req = rule.action == PolicyAction.REQUIRE_APPROVAL
            reason_msg = f"Matched policy rule '{rule.name}' ({rule.id}): {rule.description or rule.action.value}"
            return PolicyEvaluationResult(
                action=rule.action,
                matched_rule_id=rule.id,
                reason=reason_msg,
                risk_level=rule.risk_level,
                approval_required=approval_req,
            )

        # 3. Default fallback action
        return PolicyEvaluationResult(
            action=self.config.default_action,
            matched_rule_id=None,
            reason=f"No matching rule found; applying default action '{self.config.default_action.value}'",
            risk_level=RiskLevel.MEDIUM if self.config.default_action != PolicyAction.DENY else RiskLevel.HIGH,
            approval_required=(self.config.default_action == PolicyAction.REQUIRE_APPROVAL),
        )


# Global policy engine instance
policy_engine = PolicyEngine()
