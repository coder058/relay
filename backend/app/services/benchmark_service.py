"""Benchmark Runner for Relay MCP Safety Lab.

Empirically measures the wall-clock latency overhead of Relay's transparent proxy
and policy engine versus direct local MCP execution, and compares deterministic providers.
No fake or invented numbers.
"""

from datetime import datetime, timezone
import statistics
import time
from typing import Any
from app.mcp.proxy import proxy
from app.mcp.server import SafeLocalMcpServer
from app.models.provider import BenchmarkComparisonReport, ProviderSimRunResult
from app.services.provider_sim import DeterministicProviderSimulator, SIMULATED_PROVIDERS


class BenchmarkRunner:
    """Executes empirical latency benchmarks and deterministic provider comparisons."""

    @staticmethod
    async def run_latency_benchmark(iterations: int = 15) -> dict[str, Any]:
        """Measure actual wall-clock execution time for Direct vs Proxied calls.

        Executes safe read_record tool across repeated iterations to obtain
        statistically valid mean, min, max, and median latency overheads.
        """
        server = SafeLocalMcpServer()
        test_args = {"customer_id": "CUST-1001"}
        direct_times_ms: list[float] = []
        proxied_times_ms: list[float] = []

        # Warmup iteration
        await server.execute_tool("read_record", test_args)
        await proxy.process_request(
            {
                "jsonrpc": "2.0",
                "id": "warmup",
                "method": "tools/call",
                "params": {"name": "read_record", "arguments": test_args},
            },
            session_id="benchmark-warmup",
        )

        for i in range(iterations):
            # Measure Direct Execution
            t0 = time.perf_counter()
            await server.execute_tool("read_record", test_args)
            t1 = time.perf_counter()
            direct_times_ms.append((t1 - t0) * 1000.0)

            # Measure Proxied Execution (Intercept + Redact + Policy + Database Trace Write)
            t2 = time.perf_counter()
            await proxy.process_request(
                {
                    "jsonrpc": "2.0",
                    "id": f"bench_{i}",
                    "method": "tools/call",
                    "params": {"name": "read_record", "arguments": test_args},
                },
                session_id=f"bench-session-{i}",
            )
            t3 = time.perf_counter()
            proxied_times_ms.append((t3 - t2) * 1000.0)

        direct_mean = statistics.mean(direct_times_ms)
        proxied_mean = statistics.mean(proxied_times_ms)
        overhead_mean = max(0.0, proxied_mean - direct_mean)

        return {
            "iterations": iterations,
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "direct_latency_ms": {
                "mean": round(direct_mean, 3),
                "median": round(statistics.median(direct_times_ms), 3),
                "min": round(min(direct_times_ms), 3),
                "max": round(max(direct_times_ms), 3),
            },
            "proxied_latency_ms": {
                "mean": round(proxied_mean, 3),
                "median": round(statistics.median(proxied_times_ms), 3),
                "min": round(min(proxied_times_ms), 3),
                "max": round(max(proxied_times_ms), 3),
            },
            "overhead_latency_ms": {
                "mean": round(overhead_mean, 3),
                "percentage_increase": round((overhead_mean / direct_mean * 100.0) if direct_mean > 0 else 0.0, 1),
            },
            "is_measured": True,
        }

    @staticmethod
    async def run_provider_comparison(prompt: str = "Read customer account for CUST-1002") -> BenchmarkComparisonReport:
        """Run identical prompt through multiple deterministic provider simulators."""
        now_iso = datetime.now(timezone.utc).isoformat()
        results: list[ProviderSimRunResult] = []

        for provider_id in SIMULATED_PROVIDERS:
            res = await DeterministicProviderSimulator.simulate_prompt(
                provider_id=provider_id,
                prompt=prompt,
                session_id=f"comp-{provider_id}",
            )
            results.append(res)

        # Measure baseline overhead
        latency_data = await BenchmarkRunner.run_latency_benchmark(iterations=5)

        return BenchmarkComparisonReport(
            timestamp=now_iso,
            iterations=5,
            workload_name=f"Prompt: '{prompt}'",
            direct_execution_latency_ms=latency_data["direct_latency_ms"]["mean"],
            proxy_overhead_latency_ms=latency_data["overhead_latency_ms"]["mean"],
            total_proxied_latency_ms=latency_data["proxied_latency_ms"]["mean"],
            providers=results,
            summary=(
                f"Compared {len(results)} deterministic simulators. Relay proxy overhead measured at "
                f"~{latency_data['overhead_latency_ms']['mean']}ms including SQLite persistence."
            ),
            is_synthetic_workload=True,
        )
