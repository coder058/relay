"""Deterministic Agent Simulator.

Simulates multiple LLM providers making tool calls for benchmarking and demo purposes.
Explicitly labels synthetic tokens and costs. No real provider credentials required.
"""

from typing import Any
from app.models.provider import ProviderSimConfig

# Standard demo workload
DEMO_WORKLOAD_PROMPT = "List all records, then delete customer CUST-1002."

SIM_PROVIDERS = [
    ProviderSimConfig(
        provider_id="sim-anthropic-claude",
        display_name="Anthropic Claude 3 Haiku (Simulated)",
        description="Fast, cost-effective simulated model.",
        base_input_tokens=200,
        base_output_tokens=50,
        simulated_cost_per_1k_input=0.00025,
        simulated_cost_per_1k_output=0.00125,
        risk_sensitivity="strict",
    ),
    ProviderSimConfig(
        provider_id="sim-openai-gpt4o-mini",
        display_name="OpenAI GPT-4o-mini (Simulated)",
        description="Efficient lightweight simulated model.",
        base_input_tokens=180,
        base_output_tokens=55,
        simulated_cost_per_1k_input=0.00015,
        simulated_cost_per_1k_output=0.00060,
        risk_sensitivity="moderate",
    ),
]

class DeterministicAgent:
    """Generates deterministic tool calls based on a prompt and simulator config."""

    @staticmethod
    def generate_tool_call(prompt: str, config: ProviderSimConfig) -> dict[str, Any]:
        """Deterministic mapping of prompt to tool call."""
        # For our standard demo workload, we always simulate trying to delete CUST-1002
        return {
            "name": "delete_record",
            "arguments": {
                "customer_id": "CUST-1002"
            }
        }
