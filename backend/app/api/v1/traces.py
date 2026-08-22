"""Traces and Playback API Endpoint."""

from fastapi import APIRouter, HTTPException, Query
from app.models.trace import PlaybackRequest, PlaybackResult, TraceFilter
from app.services.trace_service import TraceService

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("")
async def list_traces(
    session_id: str | None = Query(None),
    tool_name: str | None = Query(None),
    policy_decision: str | None = Query(None),
    risk_level: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List execution traces with filtering and pagination."""
    filters = TraceFilter(
        session_id=session_id,
        tool_name=tool_name,
        policy_decision=policy_decision,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )
    return await TraceService.list_traces(filters)


@router.get("/{trace_id}")
async def get_trace_detail(trace_id: str):
    """Get full details of a specific trace record."""
    trace = await TraceService.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")
    return trace


@router.post("/replay", response_model=PlaybackResult)
async def replay_trace(payload: PlaybackRequest):
    """Replay a captured trace to verify deterministic policy decisions and tool outputs."""
    try:
        return await TraceService.replay_trace(
            trace_id=payload.trace_id,
            override_arguments=payload.override_arguments,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay error: {str(e)}")
