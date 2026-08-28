"""Protocol checks use the official client; all listing inputs here are synthetic."""

import asyncio
from pathlib import Path
import socket
import sys

import httpx
import pytest
import uvicorn
from mcp import Client, StdioServerParameters
from app.mcp.jobs_server import job_mcp
from app.main import app
from app.core.job_privacy import MAX_JOB_REQUEST_BYTES


PAYLOAD = {"jobs": [{"title": "Synthetic role", "description": "Python required. Remote in Spain."}], "skills": ["Python", "Rust"]}


async def assert_protocol(client):
    tools = await client.list_tools()
    assert {tool.name for tool in tools.tools} == {"search_job_board", "review_job_evidence", "export_job_review"}
    result = await client.call_tool("review_job_evidence", PAYLOAD)
    assert not result.is_error
    assert result.structured_content["jobs"][0]["skill_evidence"][0]["status"] == "mentioned"
    assert result.structured_content["jobs"][0]["application_status"] == "not_submitted"


@pytest.mark.asyncio
async def test_sdk_client_in_memory():
    async with Client(job_mcp, raise_exceptions=True) as client:
        await assert_protocol(client)


@pytest.mark.asyncio
async def test_sdk_client_over_real_stdio():
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp.jobs_server"],
                                  cwd=Path(__file__).resolve().parents[1])
    async with Client(params, raise_exceptions=True) as client:
        await assert_protocol(client)


@pytest.mark.asyncio
async def test_sdk_client_over_real_http_and_privacy(monkeypatch, setup_test_db):
    monkeypatch.setattr("app.main.db", setup_test_db)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))  # SOURCE: port zero asks the OS for an unused ephemeral port.
        port = sock.getsockname()[1]
        config = uvicorn.Config(app, log_level="error", lifespan="on")
        server = uvicorn.Server(config)
        task = asyncio.create_task(server.serve(sockets=[sock]))
        try:
            # GUESS: UNCALIBRATED GUESS test-only startup deadline/poll cadence.
            async with asyncio.timeout(15):
                while not server.started:
                    if task.done():
                        await task
                        pytest.fail("Server exited before startup")
                    await asyncio.sleep(0.05)
            base = f"http://127.0.0.1:{port}"
            async with Client(base + "/tools/mcp", raise_exceptions=True) as client:
                await assert_protocol(client)
            async with httpx.AsyncClient(base_url=base) as http:
                result = await http.post("/api/v1/jobs/review", json=PAYLOAD)
                assert result.status_code == 200
                assert result.headers["cache-control"] == "no-store"
                assert result.json()["jobs"][0]["source_text"] == PAYLOAD["jobs"][0]["description"]
                invalid = await http.post("/api/v1/jobs/review", json={"jobs": []})
                assert invalid.status_code == 422
                large = await http.post("/api/v1/jobs/review", content=b"x" * (MAX_JOB_REQUEST_BYTES + 1))
                assert large.status_code == 413
                hostile = await http.post("/tools/mcp", headers={"Host": "evil.example"}, json={})
                assert hostile.status_code == 421
        finally:
            server.should_exit = True
            await task
