"""MCP JSON-RPC 2.0 Data Models."""

from typing import Any
from pydantic import BaseModel, Field


class JsonRpcError(BaseModel):
    """Standard JSON-RPC 2.0 Error object."""

    # Standard error codes:
    # -32700: Parse error
    # -32600: Invalid Request
    # -32601: Method not found
    # -32602: Invalid params
    # -32603: Internal error
    # -32000: Policy denied (custom MCP proxy)
    # -32001: Approval required (custom MCP proxy)
    # -32002: Execution timeout (custom MCP proxy)
    # -32003: Payload too large (custom MCP proxy)
    code: int
    message: str
    data: Any | None = None


class JsonRpcRequest(BaseModel):
    """Standard JSON-RPC 2.0 Request."""

    jsonrpc: str = Field(default="2.0", pattern=r"^2\.0$")
    id: str | int | None = None
    method: str
    params: dict[str, Any] | list[Any] | None = None


class JsonRpcResponse(BaseModel):
    """Standard JSON-RPC 2.0 Response."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any | None = None
    error: JsonRpcError | None = None


class JsonRpcNotification(BaseModel):
    """JSON-RPC 2.0 Notification without ID."""

    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] | list[Any] | None = None
