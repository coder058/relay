"""MCP JSON-RPC Proxy Endpoint."""

from typing import Any
from fastapi import APIRouter, Header, Request
from app.mcp.proxy import proxy

router = APIRouter(tags=["MCP JSON-RPC"])


@router.post("/mcp/rpc")
async def handle_mcp_rpc(
    request: Request,
    x_session_id: str | None = Header(default="default-session", alias="X-Session-ID"),
) -> dict[str, Any]:
    """Intercept and handle standard MCP JSON-RPC 2.0 requests over HTTP."""
    body_bytes = await request.body()
    try:
        payload = await request.json()
    except Exception:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error: Invalid JSON payload"},
        }

    return await proxy.process_request(
        request_data=payload,
        session_id=x_session_id or "default-session",
        raw_body_bytes=len(body_bytes),
    )
