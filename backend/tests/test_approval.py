import pytest
import uuid
from app.core.approval_manager import ApprovalManager

@pytest.mark.asyncio
async def test_approval_flow():
    trace_id = f"trc_{uuid.uuid4().hex}"
    session_id = "test_session"
    tool = "delete_record"
    args = {"customer_id": "CUST-999"}
    
    # Create
    record = await ApprovalManager.create_approval(trace_id, session_id, tool, args)
    assert record.status == "pending"
    assert record.token.startswith("appr_")
    
    # Decide
    decided = await ApprovalManager.decide_approval(record.token, "approve")
    assert decided["status"] == "approved"
    
    # Consume (success)
    consumed = await ApprovalManager.consume_approval_token(record.token, trace_id, session_id, tool, args)
    assert consumed is True
    
    # Consume again (fail)
    consumed2 = await ApprovalManager.consume_approval_token(record.token, trace_id, session_id, tool, args)
    assert consumed2 is False
