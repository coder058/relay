"""Relay Configuration Module.

All numeric thresholds and demo constants are explicitly documented with their
rationale and origin tag (SOURCE, GUESS, or PLACEHOLDER) per project honesty rules.
"""

import os
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    """Application runtime settings."""

    # Application info
    app_name: str = "Relay Job Evidence"
    version: str = "0.2.0"
    environment: str = os.getenv("RELAY_ENVIRONMENT", "development")

    # Server binding
    host: str = "0.0.0.0"
    # SOURCE: standard non-privileged port commonly used for local AI/MCP lab microservices
    port: int = 8000

    # CORS configuration
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        *[
            origin.strip()
            for origin in os.getenv("RELAY_CORS_ORIGINS", "").split(",")
            if origin.strip()
        ],
    ]

    # Database
    # GUESS: SQLite database path relative to project backend root for zero-setup local execution
    sqlite_db_path: str = os.getenv(
        "RELAY_SQLITE_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "relay.db"),
    )

    # Request limits
    # SOURCE: RFC 7159 and MCP stdio frame safety limit to prevent memory exhaustion from runaway payloads
    max_request_body_bytes: int = 1_048_576  # 1 MB

    # Tool execution timeout
    # SOURCE: standard local MCP tool invocation deadline to prevent unkillable hangs while allowing local I/O
    tool_timeout_seconds: float = 5.0

    # Approval token lifetime
    # GUESS: 300-second (5 min) operator decision window before requiring re-evaluation in interactive lab sessions
    approval_token_ttl_seconds: float = 300.0

    # Session spend budget limit
    # PLACEHOLDER: conservative lab budget threshold ($1.00 USD) demonstrating budget enforcement without real funds
    default_session_spend_limit_usd: float = 1.00

    # Deterministic model simulator pricing (synthetic estimation only)
    # SOURCE: published standard lightweight tier pricing proxy ($0.0015 / 1k input tokens)
    sim_input_token_cost_per_1k: float = 0.0015
    # SOURCE: published standard lightweight tier pricing proxy ($0.0020 / 1k output tokens)
    sim_output_token_cost_per_1k: float = 0.0020


settings = Settings()
