"""Tests for Redaction Engine sanitizing sensitive credentials and PII."""

from app.core.redaction import redact_data, redact_string


def test_redact_api_keys_and_bearer_tokens():
    raw_key = "sk-1234567890abcdef1234567890abcdef"
    assert redact_string(raw_key) == "[REDACTED_API_KEY]"

    anthropic_key = "sk-ant-live9876543210abcdef9876543210abcdef"
    assert redact_string(anthropic_key) == "[REDACTED_API_KEY]"

    bearer = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    assert redact_string(bearer) == "[REDACTED_BEARER_TOKEN]"

    github_token = "ghp_123456789012345678901234567890123456"
    assert redact_string(github_token) == "[REDACTED_GITHUB_TOKEN]"


def test_redact_emails():
    text = "Contact the CEO at john.doe@enterprise.corp for details"
    sanitized = redact_string(text)
    assert "[REDACTED_EMAIL]" in sanitized
    assert "john.doe@enterprise.corp" not in sanitized


def test_redact_private_keys():
    pem = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1234567890abcdef...\n"
        "-----END RSA PRIVATE KEY-----"
    )
    sanitized = redact_string(pem)
    assert sanitized == "[REDACTED_PRIVATE_KEY]"


def test_recursive_dict_and_list_redaction():
    payload = {
        "user": {
            "name": "Alice",
            "email": "alice@example.com",
            "password": "supersecretpassword123",
            "api_key": "sk-1234567890abcdef1234567890abcdef",
        },
        "metadata": [
            {"token": "Bearer mybearertoken12345"},
            {"note": "Reach support at support@test.com"},
        ],
    }

    sanitized = redact_data(payload)

    assert sanitized["user"]["name"] == "Alice"
    assert sanitized["user"]["email"] == "[REDACTED_EMAIL]"
    assert sanitized["user"]["password"] == "[REDACTED_SECRET]"
    assert sanitized["user"]["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["metadata"][0]["token"] == "[REDACTED_SECRET]"
    assert sanitized["metadata"][1]["note"] == "Reach support at [REDACTED_EMAIL]"
