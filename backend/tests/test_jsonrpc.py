"""Tests for MCP JSON-RPC protocol handling."""

import pytest
from app.mcp.server import SafeLocalMcpServer


@pytest.mark.asyncio
async def test_tools_list_returns_valid_schema():
    server = SafeLocalMcpServer()
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    resp = await server.handle_request(req)

    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "tools" in resp["result"]
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "read_record" in tool_names
    assert "delete_record" in tool_names
    assert "list_records" in tool_names


@pytest.mark.asyncio
async def test_ping_pong():
    server = SafeLocalMcpServer()
    req = {"jsonrpc": "2.0", "id": "ping_1", "method": "ping"}
    resp = await server.handle_request(req)
    assert resp["result"] == "pong"


@pytest.mark.asyncio
async def test_unknown_method_returns_rpc_error():
    server = SafeLocalMcpServer()
    req = {"jsonrpc": "2.0", "id": 42, "method": "non_existent_method"}
    resp = await server.handle_request(req)
    assert resp["error"]["code"] == -32601
    assert "Method 'non_existent_method' not found" in resp["error"]["message"]


@pytest.mark.asyncio
async def test_missing_method_returns_invalid_request():
    server = SafeLocalMcpServer()
    req = {"jsonrpc": "2.0", "id": 99}
    resp = await server.handle_request(req)
    assert resp["error"]["code"] == -32600
