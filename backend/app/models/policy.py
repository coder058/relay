"""Policy Models for Relay MCP Security Engine."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class PolicyAction(str, Enum):
    """Decision action returned by policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class RiskLevel(str, Enum):
    """Risk severity classification for tool execution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredicateOperator(str, Enum):
    """Operator for evaluating argument predicates."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"
    IN_LIST = "in_list"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"


class ArgumentPredicate(BaseModel):
    """Predicate matching an argument within a tool call."""

    field: str
    operator: PredicateOperator = PredicateOperator.EQUALS
    value: Any = None
    description: str = ""


class PolicyRule(BaseModel):
    """A single configurable policy rule."""

    id: str
    name: str
    tool_pattern: str = "*"  # Glob pattern or exact tool name (e.g., 'delete_*', 'read_record')
    action: PolicyAction = PolicyAction.REQUIRE_APPROVAL
    risk_level: RiskLevel = RiskLevel.MEDIUM
    description: str = ""
    argument_predicates: list[ArgumentPredicate] = Field(default_factory=list)
    # GUESS: default rate limit per tool to prevent automated tool loops
    max_calls_per_minute: int | None = None
    enabled: bool = True


class PolicyConfig(BaseModel):
    """Complete policy configuration."""

    # PLACEHOLDER: conservative session spend ceiling in USD
    session_spend_limit_usd: float = 1.00
    # GUESS: default fallback action when no explicit rule matches
    default_action: PolicyAction = PolicyAction.DENY
    rules: list[PolicyRule] = Field(default_factory=list)


class PolicyEvaluationResult(BaseModel):
    """Output of policy evaluation on an incoming tool call."""

    action: PolicyAction
    matched_rule_id: str | None = None
    reason: str
    risk_level: RiskLevel = RiskLevel.LOW
    approval_required: bool = False
    approval_token: str | None = None
    approval_expires_at: float | None = None
