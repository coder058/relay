"""Benchmarks and Simulator Comparisons API Endpoint."""

from fastapi import APIRouter, Query
from app.models.provider import BenchmarkComparisonReport
from app.services.benchmark_service import BenchmarkRunner

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post("/latency")
async def measure_latency(iterations: int = Query(15, ge=1, le=100)):
    """Empirically measure wall-clock latency overhead of the Relay proxy vs direct execution."""
    return await BenchmarkRunner.run_latency_benchmark(iterations=iterations)


@router.post("/compare-providers", response_model=BenchmarkComparisonReport)
async def compare_providers(prompt: str = Query("Read customer account for CUST-1002")):
    """Run deterministic provider simulator comparisons on a prompt."""
    return await BenchmarkRunner.run_provider_comparison(prompt=prompt)
