"""Safe Local Demo MCP Server.

Provides tools/list and tools/call implementations over MCP JSON-RPC 2.0.
All tools are strictly local, memory/SQLite-isolated, and safe to run.
"""

import asyncio
import json
import sys
from typing import Any
from app.models.jsonrpc import JsonRpcError, JsonRpcResponse
from app.services.demo_fixtures import (
    create_fixture_record,
    delete_fixture_record,
    get_fixture_record,
    list_fixture_records,
    seed_fixtures_if_empty,
)

# Tool definitions exposed via tools/list
SAFE_MCP_TOOLS = [
    {
        "name": "list_records",
        "description": "List all customer accounts in the safe local demo database fixture.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_record",
        "description": "Retrieve detailed information for a specific customer ID from the local demo fixture.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier (e.g. CUST-1001)",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "create_record",
        "description": "Create a new customer account record in the safe local fixture.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Unique customer ID"},
                "name": {"type": "string", "description": "Customer full name"},
                "email": {"type": "string", "description": "Customer email address"},
                "account_balance": {"type": "number", "description": "Initial account balance in USD", "default": 0.0},
                "status": {"type": "string", "description": "Account status", "default": "active"},
            },
            "required": ["customer_id", "name", "email"],
        },
    },
    {
        "name": "delete_record",
        "description": "Destructively delete a customer record from the demo fixture. (High risk; triggers policy approval)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier to delete",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "echo",
        "description": "Safe utility tool that returns input parameters for verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo back"}
            },
            "required": ["message"],
        },
    },
    {
        "name": "get_system_metrics",
        "description": "Retrieve safe simulated system telemetry (CPU, memory, active proxy connections).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


class SafeLocalMcpServer:
    """Safe In-Process and Stdio MCP Server."""

    async def handle_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a JSON-RPC request to the appropriate method handler."""
        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params") or {}

        if not method:
            return JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(code=-32600, message="Invalid Request: 'method' is required"),
            ).model_dump()

        try:
            if method == "tools/list":
                return JsonRpcResponse(
                    id=req_id,
                    result={"tools": SAFE_MCP_TOOLS},
                ).model_dump()

            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") or {}
                result = await self.execute_tool(name, arguments)
                return JsonRpcResponse(
                    id=req_id,
                    result=result,
                ).model_dump()

            elif method == "ping":
                return JsonRpcResponse(id=req_id, result="pong").model_dump()

            else:
                return JsonRpcResponse(
                    id=req_id,
                    error=JsonRpcError(code=-32601, message=f"Method '{method}' not found"),
                ).model_dump()

        except Exception as exc:
            return JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(code=-32603, message=f"Internal Server Error: {str(exc)}"),
            ).model_dump()

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool locally against safe fixtures."""
        await seed_fixtures_if_empty()

        if name == "list_records":
            records = await list_fixture_records()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"count": len(records), "records": records}, indent=2),
                    }
                ],
                "isError": False,
            }

        elif name == "read_record":
            cust_id = arguments.get("customer_id")
            if not cust_id:
                return {
                    "content": [{"type": "text", "text": "Error: 'customer_id' is required"}],
                    "isError": True,
                }
            rec = await get_fixture_record(str(cust_id))
            if not rec:
                return {
                    "content": [{"type": "text", "text": f"Record '{cust_id}' not found in fixture."}],
                    "isError": True,
                }
            return {
                "content": [{"type": "text", "text": json.dumps(rec, indent=2)}],
                "isError": False,
            }

        elif name == "create_record":
            cust_id = str(arguments.get("customer_id", ""))
            name_val = str(arguments.get("name", ""))
            email_val = str(arguments.get("email", ""))
            bal = float(arguments.get("account_balance", 0.0))
            status_val = str(arguments.get("status", "active"))

            if not cust_id or not name_val or not email_val:
                return {
                    "content": [{"type": "text", "text": "Error: customer_id, name, and email are required"}],
                    "isError": True,
                }

            created = await create_fixture_record(cust_id, name_val, email_val, bal, status_val)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"status": "created", "record": created}, indent=2),
                    }
                ],
                "isError": False,
            }

        elif name == "delete_record":
            cust_id = str(arguments.get("customer_id", ""))
            if not cust_id:
                return {
                    "content": [{"type": "text", "text": "Error: 'customer_id' is required"}],
                    "isError": True,
                }
            deleted = await delete_fixture_record(cust_id)
            if deleted:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"status": "deleted", "customer_id": cust_id}),
                        }
                    ],
                    "isError": False,
                }
            return {
                "content": [{"type": "text", "text": f"Record '{cust_id}' not found to delete."}],
                "isError": True,
            }

        elif name == "echo":
            msg = arguments.get("message", "")
            return {
                "content": [{"type": "text", "text": f"Echo: {msg}"}],
                "isError": False,
            }

        elif name == "get_system_metrics":
            # SOURCE: Safe synthetic telemetry data
            metrics = {
                "system": "Relay Local MCP Lab Fixture",
                "cpu_load_pct": 4.2,
                "memory_used_mb": 42.8,
                "active_sessions": 1,
                "status": "nominal",
            }
            return {
                "content": [{"type": "text", "text": json.dumps(metrics, indent=2)}],
                "isError": False,
            }

        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: '{name}'"}],
                "isError": True,
            }


async def run_stdio_server():
    """Run MCP server in stdio mode for JSON-RPC MCP clients."""
    server = SafeLocalMcpServer()
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            req_data = json.loads(line.decode("utf-8").strip())
            resp_data = await server.handle_request(req_data)
            sys.stdout.write(json.dumps(resp_data) + "\n")
            sys.stdout.flush()
        except Exception as err:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(err)}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(run_stdio_server())
