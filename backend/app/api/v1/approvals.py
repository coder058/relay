"""Approvals API Endpoint."""

from fastapi import APIRouter, HTTPException
from app.core.approval_manager import ApprovalManager
from app.models.trace import ApprovalDecisionRequest

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("")
async def list_approvals():
    """List all pending approval requests."""
    return await ApprovalManager.list_pending_approvals()


@router.post("/decide")
async def decide_approval(payload: ApprovalDecisionRequest):
    """Approve or deny a pending approval request using its bound token."""
    try:
        updated = await ApprovalManager.decide_approval(
            token=payload.token,
            decision=payload.decision,
            actor=payload.actor,
            reason=payload.reason,
        )
        return {"status": "success", "approval": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
