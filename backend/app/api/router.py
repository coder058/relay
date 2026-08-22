"""API Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.approvals import router as approvals_router
from app.api.v1.benchmarks import router as benchmarks_router
from app.api.v1.demo import router as demo_router
from app.api.v1.fixtures import router as fixtures_router
from app.api.v1.health import router as health_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.policies import router as policies_router
from app.api.v1.traces import router as traces_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(mcp_router)
api_router.include_router(approvals_router)
api_router.include_router(traces_router)
api_router.include_router(policies_router)
api_router.include_router(benchmarks_router)
api_router.include_router(fixtures_router)
api_router.include_router(demo_router)
