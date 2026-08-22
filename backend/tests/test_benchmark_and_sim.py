"""Tests for Benchmark Runner and Deterministic Provider Simulator."""

import pytest
from app.services.benchmark_service import BenchmarkRunner
from app.services.provider_sim import DeterministicProviderSimulator


@pytest.mark.asyncio
async def test_deterministic_provider_simulator():
    # Fast simulator
    res_fast = await DeterministicProviderSimulator.simulate_prompt(
        provider_id="sim-fast",
        prompt="Please read customer account for CUST-1002",
    )
    assert res_fast.is_simulation is True
    assert res_fast.provider_id == "sim-fast"
    assert res_fast.wall_clock_latency_ms >= 0.0
    assert res_fast.simulated_input_tokens > 0
    assert res_fast.simulated_total_cost_usd > 0.0

    # Strict simulator
    res_strict = await DeterministicProviderSimulator.simulate_prompt(
        provider_id="sim-strict",
        prompt="Please read customer account for CUST-1002",
    )
    assert res_strict.is_simulation is True
    assert res_strict.simulated_input_tokens > res_fast.simulated_input_tokens


@pytest.mark.asyncio
async def test_latency_benchmark_overhead_measurement():
    report = await BenchmarkRunner.run_latency_benchmark(iterations=5)
    assert report["iterations"] == 5
    assert report["is_measured"] is True
    assert report["direct_latency_ms"]["mean"] >= 0.0
    assert report["proxied_latency_ms"]["mean"] >= 0.0
    assert "overhead_latency_ms" in report
