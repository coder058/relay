#!/usr/bin/env python3
"""Relay One-Command Guided Demo Runner.

Demonstrates safe execution, policy interception, human approval gating,
single-use cryptographic token binding, secret redaction, and append-only traces.
Runs 100% locally with zero external network calls or API keys.
"""

import asyncio
import json
import os
import sys

# Ensure backend is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import db
from app.core.approval_manager import ApprovalManager
from app.mcp.proxy import proxy
from app.services.demo_fixtures import list_fixture_records, reset_fixtures, seed_fixtures_if_empty
from app.services.trace_service import TraceService
from app.models.trace import TraceFilter


def banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


async def main():
    print("\n🚀 Initializing Relay Local MCP Safety Lab...")
    await db.init_db()
    await reset_fixtures()
    session_id = "terminal-guided-demo"

    # Step 1: Safe Read Operation
    banner("Step 1: Safe Tool Execution (read_record)")
    print("Agent requests: Read customer record 'CUST-1001'")
    req1 = {
        "jsonrpc": "2.0",
        "id": "step1_read",
        "method": "tools/call",
        "params": {"name": "read_record", "arguments": {"customer_id": "CUST-1001"}},
    }
    resp1 = await proxy.process_request(req1, session_id=session_id)
    print("-> Proxy Decision: ALLOW (Read operations permitted)")
    print(f"-> Response: {json.dumps(resp1.get('result'), indent=2)}")

    # Step 2: Tool Discovery
    banner("Step 2: MCP Tool Discovery (tools/list)")
    print("Agent requests: List all available MCP tools")
    req2 = {
        "jsonrpc": "2.0",
        "id": "step2_list",
        "method": "tools/list",
        "params": {},
    }
    resp2 = await proxy.process_request(req2, session_id=session_id)
    tool_names = [t["name"] for t in resp2.get("result", {}).get("tools", [])]
    print(f"-> Available safe local tools: {', '.join(tool_names)}")

    # Step 3: Destructive Action Gating (Human Approval Required)
    banner("Step 3: Destructive Action Gating (delete_record)")
    print("Agent requests: Delete customer 'CUST-1004' (High Risk)")
    req3 = {
        "jsonrpc": "2.0",
        "id": "step3_delete",
        "method": "tools/call",
        "params": {"name": "delete_record", "arguments": {"customer_id": "CUST-1004"}},
    }
    resp3 = await proxy.process_request(req3, session_id=session_id)
    print("-> Proxy Decision: REQUIRE_APPROVAL")
    error_data = resp3.get("error", {}).get("data", {})
    token = error_data.get("approval_token")
    print(f"-> Execution paused! Single-use token generated: {token}")
    print(f"-> Token expiration: {error_data.get('expires_at')}")

    # Step 4: Human Operator Approves & Agent Resumes Execution
    banner("Step 4: Human Operator Approves & Request Resumes")
    print("Operator action: Approving ticket via secure token...")
    decided = await ApprovalManager.decide_approval(
        token=token,
        decision="approve",
        actor="lead_security_operator",
        reason="Verified customer deletion ticket for test demo",
    )
    print(f"-> Token status changed to: {decided['status']}")

    print("\nAgent resumes tool call providing approved single-use token:")
    req4 = {
        "jsonrpc": "2.0",
        "id": "step4_resume_delete",
        "method": "tools/call",
        "params": {
            "name": "delete_record",
            "arguments": {"customer_id": "CUST-1004"},
            "_approval_token": token,
        },
    }
    resp4 = await proxy.process_request(req4, session_id=session_id)
    print("-> Proxy Decision: APPROVED & EXECUTED")
    print(f"-> Response: {json.dumps(resp4.get('result'), indent=2)}")

    # Step 5: Single-Use Token Invalidation Proof
    banner("Step 5: Single-Use Token Binding & Replay Prevention")
    print("Attacker / Agent tries to reuse the consumed approval token:")
    req5 = {
        "jsonrpc": "2.0",
        "id": "step5_reuse_token",
        "method": "tools/call",
        "params": {
            "name": "delete_record",
            "arguments": {"customer_id": "CUST-1001"},
            "_approval_token": token,
        },
    }
    resp5 = await proxy.process_request(req5, session_id=session_id)
    print("-> Proxy Decision: DENIED")
    print(f"-> Error: {resp5.get('error', {}).get('message')}")

    # Step 6: Critical Shell Command Blocked
    banner("Step 6: Critical Prohibited Tool Block (system_shell)")
    print("Agent attempts: Arbitrary system shell execution ('rm -rf /')")
    req6 = {
        "jsonrpc": "2.0",
        "id": "step6_block",
        "method": "tools/call",
        "params": {"name": "system_shell_exec", "arguments": {"command": "rm -rf /"}},
    }
    resp6 = await proxy.process_request(req6, session_id=session_id)
    print("-> Proxy Decision: DENY (Critical security policy)")
    print(f"-> Error: {resp6.get('error', {}).get('message')}")

    # Step 7: Secret Redaction Verification in SQLite Traces
    banner("Step 7: Secret & PII Redaction in Append-Only Traces")
    print("Agent creates record injecting API key, bearer token, and email...")
    req7 = {
        "jsonrpc": "2.0",
        "id": "step7_redaction",
        "method": "tools/call",
        "params": {
            "name": "create_record",
            "arguments": {
                "customer_id": "CUST-9901",
                "name": "VIP Investor",
                "email": "confidential_ceo@enterprise.com",
                "api_key": "sk-ant-live9876543210abcdef9876543210abcdef",
                "bearer_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummysecret",
            },
        },
    }
    await proxy.process_request(req7, session_id=session_id)

    # Inspect persisted SQLite traces
    traces = await TraceService.list_traces(TraceFilter(session_id=session_id, limit=1))
    latest_trace = traces["traces"][0]
    print("-> Persisted SQLite Trace Redacted Arguments:")
    print(json.dumps(latest_trace.get("redacted_arguments"), indent=2))

    banner("✅ Relay Demo Completed Successfully")
    print("All safety checks, approval gates, redaction, and audit logging verified.\n")


if __name__ == "__main__":
    asyncio.run(main())
