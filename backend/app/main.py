"""Relay MCP Safety Lab - Main FastAPI Application."""

from contextlib import asynccontextmanager
import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings
from app.core.database import db
from app.services.demo_fixtures import seed_fixtures_if_empty
from app.api.v1.fixtures import reset_demo_fixtures
from app.api.v1.mcp import handle_mcp_rpc


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    # Initialize SQLite tables and seed demo fixture on start
    await db.init_db()
    await seed_fixtures_if_empty()
    yield
    # Cleanup if needed on shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Portfolio-quality local MCP safety, policy enforcement, and observability lab.",
    lifespan=lifespan,
)

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
