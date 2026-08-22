"""Guided Demo Scenarios API Endpoint."""

import time
from fastapi import APIRouter, HTTPException
from app.mcp.proxy import proxy

router = APIRouter(prefix="/demo", tags=["Guided Demo"])


@router.post("/step/{step_id}")
async def trigger_demo_step(step_id: int):
    """Execute a specific guided demo scenario:

    Step 1: Safe read tool execution -> Policy ALLOW
    Step 2: Utility list tool execution -> Policy ALLOW
    Step 3: Destructive delete tool execution -> Policy REQUIRE_APPROVAL (Pauses & issues single-use token)
    Step 4: Dangerous shell command simulation -> Policy DENY
    Step 5: Sensitive parameter injection -> REDACTED before storage
    """
    session_id = "guided-demo-session"

    if step_id == 1:
        # Step 1: Safe read
        payload = {
            "jsonrpc": "2.0",
            "id": f"demo_read_{int(time.time())}",
            "method": "tools/call",
            "params": {"name": "read_record", "arguments": {"customer_id": "CUST-1001"}},
        }
        resp = await proxy.process_request(payload, session_id=session_id)
        return {
            "step": 1,
            "title": "Safe Read Operation",
            "description": "Agent reads record 'CUST-1001'. Relay policy automatically allows read operations.",
            "response": resp,
        }

    elif step_id == 2:
        # Step 2: List records
        payload = {
            "jsonrpc": "2.0",
            "id": f"demo_list_{int(time.time())}",
            "method": "tools/call",
            "params": {"name": "list_records", "arguments": {}},
        }
        resp = await proxy.process_request(payload, session_id=session_id)
        return {
            "step": 2,
            "title": "Safe Discovery List",
            "description": "Agent lists all customer records. Relay policy evaluates and permits tool discovery.",
            "response": resp,
        }

    elif step_id == 3:
        # Step 3: Risky delete requiring human approval
        payload = {
            "jsonrpc": "2.0",
            "id": f"demo_del_{int(time.time())}",
            "method": "tools/call",
            "params": {"name": "delete_record", "arguments": {"customer_id": "CUST-1004"}},
        }
        resp = await proxy.process_request(payload, session_id=session_id)
        return {
            "step": 3,
            "title": "Destructive Action Gating (Human Approval Required)",
            "description": (
                "Agent attempts to delete customer 'CUST-1004'. Relay intercepts and pauses execution, "
                "generating an expiring single-use approval ticket. Human operator can approve or deny in dashboard."
            ),
            "response": resp,
        }

    elif step_id == 4:
        # Step 4: Prohibited arbitrary execution
        payload = {
            "jsonrpc": "2.0",
            "id": f"demo_exec_{int(time.time())}",
            "method": "tools/call",
            "params": {"name": "system_shell_exec", "arguments": {"command": "rm -rf /"}},
        }
        resp = await proxy.process_request(payload, session_id=session_id)
        return {
            "step": 4,
            "title": "Critical Policy Block",
            "description": "Agent attempts arbitrary shell execution. Relay policy engine strictly denies execution.",
            "response": resp,
        }

    elif step_id == 5:
        # Step 5: Redaction of API keys and PII
        payload = {
            "jsonrpc": "2.0",
            "id": f"demo_redact_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "create_record",
                "arguments": {
                    "customer_id": "CUST-9901",
                    "name": "Secret VIP User",
                    "email": "confidential_ceo@enterprise.com",
                    # SOURCE: synthetic redaction-demo fixture; not a real account balance.
                    "account_balance": 99000.0,
                    "api_key": "sk-ant-live0123456789abcdef0123456789abcdef",
                    "bearer_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummysecret",
                },
            },
        }
        resp = await proxy.process_request(payload, session_id=session_id)
        return {
            "step": 5,
            "title": "Secret & PII Redaction",
            "description": (
                "Agent sends tool call with sensitive credentials (API key, bearer token, email). "
                "Relay redacts all secrets before logging into SQLite traces and browser payloads."
            ),
            "response": resp,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Invalid demo step '{step_id}'. Valid steps are 1 through 5.")
