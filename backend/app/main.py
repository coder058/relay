"""Relay Job Evidence - Main FastAPI application."""

from contextlib import asynccontextmanager
import time
import uuid
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings
from app.core.database import db
from app.services.demo_fixtures import seed_fixtures_if_empty
from app.api.v1.fixtures import reset_demo_fixtures
from app.api.v1.mcp import handle_mcp_rpc
from app.mcp.jobs_server import job_mcp
from app.core.job_privacy import JobPrivacyMiddleware, MAX_JOB_REQUEST_BYTES
from mcp.server.transport_security import TransportSecuritySettings

# SOURCE: exact public service hostname verified via Cloud Run, plus local development.
# Override with a comma-separated allowlist when deploying to another service.
job_http = job_mcp.streamable_http_app(
    stateless_http=True, json_response=True, max_request_body_size=MAX_JOB_REQUEST_BYTES,
    transport_security=TransportSecuritySettings(
        allowed_hosts=["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*", *[
            value.strip() for value in os.getenv("RELAY_MCP_HOSTS", "relay-backend-r3ux6b3uwa-ew.a.run.app").split(",") if value.strip()]],
        allowed_origins=settings.cors_origins,
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    # Initialize SQLite tables and seed demo fixture on start
    await db.init_db()
    await seed_fixtures_if_empty()
    async with job_mcp.session_manager.run():
        yield
    # Cleanup if needed on shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Read-only job evidence desk with MCP tools. Historical synthetic safety lab is isolated.",
    lifespan=lifespan,
)
app.add_middleware(JobPrivacyMiddleware)

# CORS middleware for local frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    """Assign a unique X-Request-ID and calculate server processing duration."""
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
    t_start = time.perf_counter()

    response: Response = await call_next(request)

    duration_ms = (time.perf_counter() - t_start) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    return response


# Include API v1 router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root metadata endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": "/api/v1",
    }


@app.get("/health")
async def compatibility_health():
    """Compatibility health endpoint for the local smoke test."""
    return {"status": "ok", "version": settings.version}


@app.post("/api/demo/reset")
async def compatibility_reset_fixtures():
    """Compatibility alias for resetting the safe local demo fixture."""
    records = await reset_demo_fixtures()
    return {"status": "success", "records": records["records"]}


@app.post("/api/mcp/proxy")
async def compatibility_mcp_proxy(request: Request):
    """Compatibility alias for the original local proxy smoke-test path."""
    return await handle_mcp_rpc(request, "default-session")


# SOURCE: mounted SDK app serves its default /mcp at /tools/mcp.
app.mount("/tools", job_http)
