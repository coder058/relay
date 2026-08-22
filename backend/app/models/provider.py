"""Provider Simulator and Benchmark Models."""

from typing import Any
from pydantic import BaseModel


class ProviderSimConfig(BaseModel):
    """Configuration for a deterministic provider simulator."""

    provider_id: str
    display_name: str
    description: str
    # SOURCE: lightweight simulation base token parameters
    base_input_tokens: int = 150
    base_output_tokens: int = 80
    simulated_cost_per_1k_input: float = 0.0015
    simulated_cost_per_1k_output: float = 0.0020
    # Simulated execution profile (deterministic behavior)
    risk_sensitivity: str = "moderate"  # "permissive" | "moderate" | "strict"


class ProviderSimRunResult(BaseModel):
    """Execution output from a deterministic provider simulation."""

    provider_id: str
    provider_name: str
    prompt: str
    generated_tool_call: dict[str, Any]
    wall_clock_latency_ms: float
    simulated_input_tokens: int
    simulated_output_tokens: int
    simulated_total_cost_usd: float
    policy_decision: str
    is_simulation: bool = True  # Always explicit


class BenchmarkComparisonReport(BaseModel):
    """Report comparing multiple deterministic provider simulators on identical workloads."""

    timestamp: str
    iterations: int
    workload_name: str
    # Measured overheads (actual wall-clock)
    direct_execution_latency_ms: float
    proxy_overhead_latency_ms: float
    total_proxied_latency_ms: float
    # Provider comparisons
    providers: list[ProviderSimRunResult]
    summary: str
    is_synthetic_workload: bool = True
