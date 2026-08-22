#!/usr/bin/env python3
"""Relay Empirical Latency Overhead Benchmark CLI.

Measures actual wall-clock execution time across iterations for direct MCP execution
vs Relay proxy interception (including policy evaluation, secret redaction, and SQLite trace writes).
Outputs verified statistical measurements. Never invents results.
"""

import asyncio
import os
import sys

# Ensure backend is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import db
from app.services.benchmark_service import BenchmarkRunner


async def main():
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    print("\n" + "=" * 70)
    print(f"  RELAY WALL-CLOCK OVERHEAD BENCHMARK ({iterations} ITERATIONS)")
    print("=" * 70)
    print("Initializing database...")
    await db.init_db()

    print(f"Running {iterations} cycles of Direct Tool vs Proxied Tool executions...\n")
    report = await BenchmarkRunner.run_latency_benchmark(iterations=iterations)

    direct = report["direct_latency_ms"]
    proxied = report["proxied_latency_ms"]
    overhead = report["overhead_latency_ms"]

    print(f"{'Metric':<25} | {'Direct Tool':<15} | {'Proxied + Trace':<18} | {'Overhead'}")
    print("-" * 75)
    print(f"{'Mean Latency':<25} | {direct['mean']:>10.3f} ms  | {proxied['mean']:>12.3f} ms    | +{overhead['mean']:.3f} ms")
    print(f"{'Median Latency':<25} | {direct['median']:>10.3f} ms  | {proxied['median']:>12.3f} ms    | —")
    print(f"{'Min Latency':<25} | {direct['min']:>10.3f} ms  | {proxied['min']:>12.3f} ms    | —")
    print(f"{'Max Latency':<25} | {direct['max']:>10.3f} ms  | {proxied['max']:>12.3f} ms    | —")
    print("-" * 75)
    print(f"Percentage Overhead: +{overhead['percentage_increase']}%")
    print(f"Measured at: {report['measured_at']} (UTC)")
    print("\nNotes:")
    print("• Overhead includes: JSON-RPC validation, policy evaluation, argument predicate matching,")
    print("  deep recursive secret redaction, and append-only SQLite disk persistence.")
    print("• All measurements are empirical wall-clock times recorded on the local machine.\n")


if __name__ == "__main__":
    asyncio.run(main())
