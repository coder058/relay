"""Redaction Engine for Relay MCP Safety Lab.

Scans requests, responses, and tool arguments recursively to sanitize API keys,
bearer tokens, passwords, cookies, private keys, and email addresses before persistence.
"""

import re
from typing import Any

# Sensitive key names (case-insensitive match)
SENSITIVE_KEY_PATTERNS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "api-key",
    "token",
    "access_token",
    "auth_token",
    "authorization",
    "bearer",
    "private_key",
    "privkey",
    "cookie",
    "cookies",
    "session_secret",
    "jwt",
    "card_number",
    "cvv",
}

# Regex patterns for high-entropy / structured secrets in text values
PATTERNS = [
    # API keys / Bearer tokens (OpenAI, Anthropic, GitHub, Slack, AWS, generic)
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "[REDACTED_BEARER_TOKEN]"),
    (re.compile(r"\b(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9_-]{20,})\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36})\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "[REDACTED_AWS_KEY]"),
    # Private keys (PEM format)
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
            re.MULTILINE,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    # Email addresses
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # Cookie strings
    (
        re.compile(r"(?:sessionid|session_id|connect\.sid|auth_token)=([^\s;]+)", re.IGNORECASE),
        "session_id=[REDACTED_COOKIE]",
    ),
]


def redact_string(text: str) -> str:
    """Apply all regex redaction rules to a string."""
    if not isinstance(text, str) or not text:
        return text

    sanitized = text
    for pattern, replacement in PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def redact_data(data: Any, parent_key: str | None = None) -> Any:
    """Recursively redact sensitive content in JSON-compatible structures.

    Args:
        data: Primitive, dict, or list to redact.
        parent_key: The dictionary key associated with this data (if applicable).

    Returns:
        Sanitized copy of data with sensitive values redacted.
    """
    if data is None:
        return None

    # If the dictionary key itself indicates a sensitive field, redact the entire value
    if parent_key and parent_key.lower() in SENSITIVE_KEY_PATTERNS:
        if isinstance(data, (str, int, float, bool)):
            return "[REDACTED_SECRET]"
        if isinstance(data, dict):
            return {k: "[REDACTED_SECRET]" for k in data}
        if isinstance(data, list):
            return ["[REDACTED_SECRET]" for _ in data]

    if isinstance(data, str):
        return redact_string(data)

    if isinstance(data, dict):
        return {k: redact_data(v, parent_key=k) for k, v in data.items()}

    if isinstance(data, list):
        return [redact_data(item, parent_key=parent_key) for item in data]

    if isinstance(data, tuple):
        return tuple(redact_data(item, parent_key=parent_key) for item in data)

    return data
