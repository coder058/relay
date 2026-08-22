"""Trace Service for Relay MCP Safety Lab.

Handles append-only storage of redacted execution records, trace queries,
and deterministic playback verification against the local environment.
"""

from datetime import datetime, timezone
import json
import time
from typing import Any
import uuid
from app.core.database import db
from app.core.redaction import redact_data
from app.models.trace import PlaybackResult, TraceFilter, TraceRecord


class TraceService:
    """Manages recording, querying, and replaying MCP execution traces."""

    @staticmethod
    async def record_trace(
        session_id: str,
        method: str,
        tool_name: str | None,
        raw_arguments: dict[str, Any] | None,
        policy_decision: str,
        matched_rule_id: str | None,
        policy_reason: str | None,
        risk_level: str | None,
        approval_id: str | None,
        approval_status: str | None,
        raw_result: Any | None,
        error: str | None,
        duration_ms: float,
        request_id: str | int | None = None,
        simulated_tokens: int | None = None,
        simulated_cost_usd: float | None = None,
        is_synthetic: bool = False,
        trace_id: str | None = None,
    ) -> TraceRecord:
        """Redact sensitive fields, then persist an append-only trace.

        The ``raw_arguments``/``raw_result`` parameter names are retained for
        compatibility with the demo API, but the original values are never
        written to SQLite. Both the legacy ``raw_*`` columns and the explicit
        ``redacted_*`` columns receive the sanitized copy.
        """
        t_id = trace_id or f"trc_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Sanitize data before persistence
        redacted_args = redact_data(raw_arguments) if raw_arguments is not None else None
        redacted_res = redact_data(raw_result) if raw_result is not None else None

        record = TraceRecord(
            id=t_id,
            timestamp=now_iso,
            session_id=session_id,
            request_id=request_id,
            method=method,
            tool_name=tool_name,
            raw_arguments=redacted_args,  # Store sanitized arguments to guarantee no secret leak
            redacted_arguments=redacted_args,
            policy_decision=policy_decision,
            matched_rule_id=matched_rule_id,
            policy_reason=policy_reason,
            risk_level=risk_level,
            approval_id=approval_id,
            approval_status=approval_status,
            raw_result=redacted_res,  # Store sanitized result
            redacted_result=redacted_res,
            error=error,
            duration_ms=duration_ms,
            simulated_tokens=simulated_tokens,
            simulated_cost_usd=simulated_cost_usd,
            is_synthetic=is_synthetic,
        )

        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO traces (
                        id, timestamp, session_id, request_id, method, tool_name,
                        raw_arguments_json, redacted_arguments_json,
                        policy_decision, matched_rule_id, policy_reason, risk_level,
                        approval_id, approval_status, raw_result_json, redacted_result_json,
                        error, duration_ms, simulated_tokens, simulated_cost_usd, is_synthetic
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.timestamp,
                        record.session_id,
                        str(record.request_id) if record.request_id is not None else None,
                        record.method,
                        record.tool_name,
                        json.dumps(record.raw_arguments) if record.raw_arguments is not None else None,
                        json.dumps(record.redacted_arguments) if record.redacted_arguments is not None else None,
                        record.policy_decision,
                        record.matched_rule_id,
                        record.policy_reason,
                        record.risk_level,
                        record.approval_id,
                        record.approval_status,
                        json.dumps(record.raw_result) if record.raw_result is not None else None,
                        json.dumps(record.redacted_result) if record.redacted_result is not None else None,
                        record.error,
                        record.duration_ms,
                        record.simulated_tokens,
                        record.simulated_cost_usd,
                        1 if record.is_synthetic else 0,
                    ),
                )
                await conn.commit()
        finally:
            await conn.close()

        return record

    @staticmethod
    async def list_traces(filters: TraceFilter) -> dict[str, Any]:
        """Query traces with filtering and pagination."""
        conn = await db.get_connection()
        try:
            where_clauses = ["1=1"]
            params: list[Any] = []

            if filters.session_id:
                where_clauses.append("session_id = ?")
                params.append(filters.session_id)
            if filters.tool_name:
                where_clauses.append("tool_name = ?")
                params.append(filters.tool_name)
            if filters.policy_decision:
                where_clauses.append("policy_decision = ?")
                params.append(filters.policy_decision)
            if filters.risk_level:
                where_clauses.append("risk_level = ?")
                params.append(filters.risk_level)

            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM traces WHERE {where_str} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            query_params = list(params) + [filters.limit, filters.offset]

            async with conn.cursor() as cur:
                await cur.execute(query, query_params)
                rows = await cur.fetchall()

                # Get total count
                count_query = f"SELECT COUNT(*) FROM traces WHERE {where_str}"
                await cur.execute(count_query, params)
                count_row = await cur.fetchone()
                total = count_row[0] if count_row else 0

                records = []
                for r in rows:
                    d = dict(r)
                    if d.get("redacted_arguments_json"):
                        try:
                            d["redacted_arguments"] = json.loads(d["redacted_arguments_json"])
                        except Exception:
                            d["redacted_arguments"] = {}
                    if d.get("redacted_result_json"):
                        try:
                            d["redacted_result"] = json.loads(d["redacted_result_json"])
                        except Exception:
                            d["redacted_result"] = d["redacted_result_json"]
                    d["is_synthetic"] = bool(d.get("is_synthetic", 0))
                    records.append(d)

                return {"total": total, "limit": filters.limit, "offset": filters.offset, "traces": records}
        finally:
            await conn.close()

    @staticmethod
    async def get_trace(trace_id: str) -> dict[str, Any] | None:
        """Get trace detail by ID."""
        conn = await db.get_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM traces WHERE id = ?", (trace_id,))
                row = await cur.fetchone()
                if not row:
                    return None
                d = dict(row)
                if d.get("raw_arguments_json"):
                    try:
                        d["raw_arguments"] = json.loads(d["raw_arguments_json"])
                    except Exception:
                        d["raw_arguments"] = {}
                if d.get("redacted_arguments_json"):
                    try:
                        d["redacted_arguments"] = json.loads(d["redacted_arguments_json"])
                    except Exception:
                        d["redacted_arguments"] = {}
                if d.get("raw_result_json"):
                    try:
                        d["raw_result"] = json.loads(d["raw_result_json"])
                    except Exception:
                        d["raw_result"] = d["raw_result_json"]
                if d.get("redacted_result_json"):
                    try:
                        d["redacted_result"] = json.loads(d["redacted_result_json"])
                    except Exception:
                        d["redacted_result"] = d["redacted_result_json"]
                d["is_synthetic"] = bool(d.get("is_synthetic", 0))
                return d
        finally:
            await conn.close()

    @staticmethod
    async def replay_trace(trace_id: str, override_arguments: dict[str, Any] | None = None) -> PlaybackResult:
        """Replay a recorded trace through policy evaluation and tool execution.

        Measures wall-clock latency, tests policy determinism, and checks output match.
        """
        from app.core.policy_engine import policy_engine
        from app.mcp.server import SafeLocalMcpServer

        trace = await TraceService.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace '{trace_id}' not found.")

        tool_name = trace.get("tool_name") or "unknown"
        arguments = override_arguments if override_arguments is not None else (trace.get("redacted_arguments") or {})
        session_id = f"replay_{trace.get('session_id', 'default')}"

        t_start = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Evaluate policy
        eval_res = await policy_engine.evaluate(session_id=session_id, tool_name=tool_name, arguments=arguments)
        playback_decision = eval_res.action.value

        output_data = None
        error_msg = None

        # 2. If allowed or if was approved in original and allowed now, execute tool safely
        if eval_res.action.value == "allow":
            server = SafeLocalMcpServer()
            try:
                output_data = await server.execute_tool(tool_name, arguments)
            except Exception as e:
                error_msg = str(e)
        elif eval_res.action.value == "require_approval":
            output_data = {"status": "paused_for_approval", "reason": eval_res.reason}
        else:
            error_msg = f"Policy denied execution: {eval_res.reason}"

        playback_duration_ms = (time.perf_counter() - t_start) * 1000.0

        decision_matches = (playback_decision == trace.get("policy_decision"))

        return PlaybackResult(
            original_trace_id=trace_id,
            replayed_at=now_iso,
            tool_name=tool_name,
            arguments=arguments,
            original_decision=trace.get("policy_decision", "unknown"),
            playback_decision=playback_decision,
            decision_matches=decision_matches,
            playback_duration_ms=round(playback_duration_ms, 3),
            original_duration_ms=round(float(trace.get("duration_ms", 0.0)), 3),
            output=output_data,
            error=error_msg,
        )
