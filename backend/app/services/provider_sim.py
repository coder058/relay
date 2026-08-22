"""Deterministic Provider Simulators for Relay MCP Safety Lab.

Simulates two distinct model providers (Fast Model vs Strict Guarded Model)
deterministically without calling external paid APIs or leaking keys.
All synthetic token and cost fields are explicitly labelled as simulated.
"""

import time
from app.mcp.proxy import proxy
from app.models.provider import ProviderSimConfig, ProviderSimRunResult

SIMULATED_PROVIDERS = {
    "sim-fast": ProviderSimConfig(
        provider_id="sim-fast",
        display_name="Fast-Deterministic-Sim (Simulated)",
        description="Lightweight simulated model optimized for fast responses and direct parameter emission",
        base_input_tokens=120,
        base_output_tokens=65,
        simulated_cost_per_1k_input=0.0010,
        simulated_cost_per_1k_output=0.0015,
        risk_sensitivity="moderate",
    ),
    "sim-strict": ProviderSimConfig(
        provider_id="sim-strict",
        display_name="Strict-Guarded-Sim (Simulated)",
        description="Rigorous simulated model with verbose prompt context and structured parameter validation",
        base_input_tokens=350,
        base_output_tokens=140,
        simulated_cost_per_1k_input=0.0030,
        simulated_cost_per_1k_output=0.0060,
        risk_sensitivity="strict",
    ),
}


class DeterministicProviderSimulator:
    """Runs deterministic provider tool-calling scenarios without real external LLMs."""

    @staticmethod
    async def simulate_prompt(
        provider_id: str,
        prompt: str,
        session_id: str = "sim-benchmark-session",
    ) -> ProviderSimRunResult:
        """Deterministically map a user prompt to a tool call and execute via Relay proxy."""
        config = SIMULATED_PROVIDERS.get(provider_id)
        if not config:
            raise ValueError(f"Unknown simulated provider '{provider_id}'. Available: {list(SIMULATED_PROVIDERS.keys())}")

        # Deterministic tool call generation based on prompt keywords
        prompt_lower = prompt.lower()
        if "delete" in prompt_lower or "remove" in prompt_lower:
            tool_name = "delete_record"
            cust_id = "CUST-1001" if "1001" in prompt_lower else "CUST-1004"
            arguments = {"customer_id": cust_id}
        elif "create" in prompt_lower or "add" in prompt_lower or "new" in prompt_lower:
            tool_name = "create_record"
            arguments = {
                "customer_id": "CUST-9999",
                "name": "Simulated User",
                "email": "simulated@example.com",
                "account_balance": 250.0,
                "status": "active",
            }
        elif "list" in prompt_lower or "all" in prompt_lower:
            tool_name = "list_records"
            arguments = {}
        elif "metrics" in prompt_lower or "system" in prompt_lower:
            tool_name = "get_system_metrics"
            arguments = {}
        else:
            tool_name = "read_record"
            arguments = {"customer_id": "CUST-1002"}

        input_tokens = config.base_input_tokens + len(prompt) // 4
        output_tokens = config.base_output_tokens + len(str(arguments)) // 4
        cost = (input_tokens / 1000.0) * config.simulated_cost_per_1k_input + (
            output_tokens / 1000.0
        ) * config.simulated_cost_per_1k_output

        mcp_payload = {
            "jsonrpc": "2.0",
            "id": f"sim_req_{int(time.time()*1000)}",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        t_start = time.perf_counter()
        resp = await proxy.process_request(mcp_payload, session_id=session_id)
        wall_clock_ms = (time.perf_counter() - t_start) * 1000.0

        decision = "allow"
        if resp.get("error"):
            code = resp["error"].get("code")
            if code == -32001:
                decision = "require_approval"
            elif code == -32000:
                decision = "deny"
            else:
                decision = "error"

        return ProviderSimRunResult(
            provider_id=config.provider_id,
            provider_name=config.display_name,
            prompt=prompt,
            generated_tool_call={"name": tool_name, "arguments": arguments},
            wall_clock_latency_ms=round(wall_clock_ms, 3),
            simulated_input_tokens=input_tokens,
            simulated_output_tokens=output_tokens,
            simulated_total_cost_usd=round(cost, 6),
            policy_decision=decision,
            is_simulation=True,
        )
