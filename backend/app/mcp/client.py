"""MCP Stdio Proxy Client.

Spawns the safe local MCP server via stdio and proxies JSON-RPC requests,
enabling policy evaluation and tracing in the proxy layer.
"""

import asyncio
import json
import sys
from typing import Any
from app.models.jsonrpc import JsonRpcRequest

class StdioMcpClient:
    """Manages the subprocess for the stdio MCP server."""

    def __init__(self, command: list[str]):
        self.command = command
        self.process: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,
        )

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for the response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP process not running")

        async with self.lock: # Wait, no, we need to map IDs to futures if we want concurrent requests, but for demo, a simple lock is fine.
            self._request_id += 1
            req_id = str(self._request_id)
            req = JsonRpcRequest(id=req_id, method=method, params=params)
            
            payload = req.model_dump_json() + "\n"
            self.process.stdin.write(payload.encode("utf-8"))
            await self.process.stdin.drain()

            line = await self.process.stdout.readline()
            if not line:
                raise RuntimeError("Unexpected EOF from MCP server")
            
            resp_data = json.loads(line.decode("utf-8").strip())
            return resp_data

    @property
    def lock(self):
        return self._lock

mcp_client = StdioMcpClient([sys.executable, "-m", "app.mcp.server"])
