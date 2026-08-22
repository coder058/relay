"""Tests for MCP Transparent Security Proxy."""

import pytest
from app.config import settings
from app.mcp.proxy import proxy


@pytest.mark.asyncio
async def test_proxy_executes_safe_tool():
    req = {
        "jsonrpc": "2.0",
        "id": "safe_read_1",
        "method": "tools/call",
        "params": {"name": "read_record", "arguments": {"customer_id": "CUST-1001"}},
    }
    resp = await proxy.process_request(req, session_id="test-proxy-safe")
    assert resp.get("error") is None
    assert "result" in resp


@pytest.mark.asyncio
async def test_proxy_enforces_max_request_size():
    oversized_bytes = settings.max_request_body_bytes + 500
    req = {
        "jsonrpc": "2.0",
        "id": "oversized_1",
        "method": "tools/call",
        "params": {"name": "read_record", "arguments": {}},
    }
    resp = await proxy.process_request(req, session_id="test-size", raw_body_bytes=oversized_bytes)
    assert resp.get("error") is not None
    assert resp["error"]["code"] == -32003
    assert "Payload too large" in resp["error"]["message"]
