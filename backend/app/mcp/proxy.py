"""Transparent MCP JSON-RPC Proxy.

Intercepts tools/list and tools/call requests, enforces security policies,
manages human-in-the-loop approval gating, records sanitized traces,
and executes safe local MCP tools with hard timeout limits.
"""

import asyncio
import time
from typing import Any
import uuid
from app.config import settings
from app.core.approval_manager import ApprovalManager
from app.core.policy_engine import policy_engine
from app.mcp.server import SafeLocalMcpServer
from app.models.jsonrpc import JsonRpcError, JsonRpcResponse
from app.models.policy import PolicyAction
from app.services.trace_service import TraceService


class McpProxy:
    """Transparent MCP JSON-RPC Interceptor & Security Proxy."""

    def __init__(self, backend_server: SafeLocalMcpServer | None = None):
        self.backend = backend_server or SafeLocalMcpServer()

    async def process_request(
        self,
        request_data: dict[str, Any],
        session_id: str = "default-session",
        raw_body_bytes: int = 0,
    ) -> dict[str, Any]:
        """Process an incoming MCP JSON-RPC request through the security proxy."""
        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params") or {}
        trace_id = f"trc_{uuid.uuid4().hex[:12]}"

        t_start = time.perf_counter()

        # 1. Size constraint check
        if raw_body_bytes > settings.max_request_body_bytes:
            err_resp = JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(
                    code=-32003,
                    message=f"Payload too large: {raw_body_bytes} bytes exceeds {settings.max_request_body_bytes} bytes limit",
                ),
            ).model_dump()
            await TraceService.record_trace(
                session_id=session_id,
                method=method or "unknown",
                tool_name=None,
                raw_arguments=None,
                policy_decision="denied_oversized",
                matched_rule_id=None,
                policy_reason="Request size limit exceeded",
                risk_level="high",
                approval_id=None,
                approval_status=None,
                raw_result=None,
                error=err_resp["error"]["message"],
                duration_ms=(time.perf_counter() - t_start) * 1000.0,
                request_id=req_id,
                trace_id=trace_id,
            )
            return err_resp

        if not method:
            return JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(code=-32600, message="Invalid Request: 'method' is required"),
            ).model_dump()

        # 2. Transparent passthrough for discovery methods (e.g. tools/list, ping)
        if method == "tools/list" or method == "ping":
            backend_resp = await self.backend.handle_request(request_data)
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            await TraceService.record_trace(
                session_id=session_id,
                method=method,
                tool_name=None,
                raw_arguments=params if isinstance(params, dict) else None,
                policy_decision="allow",
                matched_rule_id="passthrough",
                policy_reason=f"Safe discovery method '{method}' allowed",
                risk_level="low",
                approval_id=None,
                approval_status=None,
                raw_result=backend_resp.get("result"),
                error=backend_resp.get("error", {}).get("message") if backend_resp.get("error") else None,
                duration_ms=duration_ms,
                request_id=req_id,
                trace_id=trace_id,
            )
            return backend_resp

        # 3. Intercept and evaluate tools/call
        if method == "tools/call":
            if not isinstance(params, dict):
                return JsonRpcResponse(
                    id=req_id,
                    error=JsonRpcError(code=-32602, message="Invalid params: expected object for tools/call"),
                ).model_dump()

            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            # Check if an approval token is attached
            provided_token = params.get("_approval_token") or (
                arguments.get("_approval_token") if isinstance(arguments, dict) else None
            )

            if isinstance(arguments, dict) and "_approval_token" in arguments:
                # Strip internal approval token from tool argument map before evaluation/execution
                arguments = {k: v for k, v in arguments.items() if k != "_approval_token"}

            if not tool_name:
                return JsonRpcResponse(
                    id=req_id,
                    error=JsonRpcError(code=-32602, message="Invalid params: 'name' is required"),
                ).model_dump()

            # Estimate synthetic cost
            # SOURCE: lightweight simulation token heuristic for demo session spend estimation
            estimated_tokens = len(str(arguments)) // 4 + 100
            estimated_cost = (estimated_tokens / 1000.0) * settings.sim_input_token_cost_per_1k

            # Policy Evaluation
            eval_result = await policy_engine.evaluate(
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                estimated_cost_usd=estimated_cost,
            )

            # Case A: Denied by Policy
            if eval_result.action == PolicyAction.DENY:
                duration_ms = (time.perf_counter() - t_start) * 1000.0
                err_resp = JsonRpcResponse(
                    id=req_id,
                    error=JsonRpcError(
                        code=-32000,
                        message=f"Policy Denied: {eval_result.reason}",
                        data={"tool": tool_name, "rule_id": eval_result.matched_rule_id},
                    ),
                ).model_dump()

                await TraceService.record_trace(
                    session_id=session_id,
                    method=method,
                    tool_name=tool_name,
                    raw_arguments=arguments,
                    policy_decision="deny",
                    matched_rule_id=eval_result.matched_rule_id,
                    policy_reason=eval_result.reason,
                    risk_level=eval_result.risk_level.value,
                    approval_id=None,
                    approval_status="none",
                    raw_result=None,
                    error=err_resp["error"]["message"],
                    duration_ms=duration_ms,
                    request_id=req_id,
                    simulated_tokens=estimated_tokens,
                    simulated_cost_usd=estimated_cost,
                    trace_id=trace_id,
                )
                return err_resp

            # Case B: Require Approval
            if eval_result.action == PolicyAction.REQUIRE_APPROVAL:
                # Check if caller presented an approved token
                if provided_token:
                    consumed = await ApprovalManager.consume_approval_token(
                        token=provided_token,
                        trace_id=trace_id,  # Or original trace bound token
                        session_id=session_id,
                        tool_name=tool_name,
                        arguments=arguments,
                    )
                    # If direct match or session-bound match
                    if not consumed:
                        # Try validating if token was approved for this session/tool/args
                        approval = await ApprovalManager.get_approval_by_token(provided_token)
                        if approval and approval.get("status") == "approved":
                            consumed = await ApprovalManager.consume_approval_token(
                                token=provided_token,
                                trace_id=approval["trace_id"],
                                session_id=approval["session_id"],
                                tool_name=approval["tool_name"],
                                arguments=arguments,
                            )

                    if consumed:
                        # Approved & consumed token -> proceed with execution
                        return await self._execute_and_record(
                            req_id=req_id,
                            session_id=session_id,
                            method=method,
                            tool_name=tool_name,
                            arguments=arguments,
                            t_start=t_start,
                            policy_decision="approved",
                            matched_rule_id=eval_result.matched_rule_id,
                            policy_reason=f"Execution resumed via approved token: {provided_token}",
                            risk_level=eval_result.risk_level.value,
                            approval_token=provided_token,
                            approval_status="consumed",
                            estimated_tokens=estimated_tokens,
                            estimated_cost=estimated_cost,
                            trace_id=trace_id,
                        )
                    else:
                        duration_ms = (time.perf_counter() - t_start) * 1000.0
                        err_resp = JsonRpcResponse(
                            id=req_id,
                            error=JsonRpcError(
                                code=-32001,
                                message="Invalid, expired, or already-consumed approval token",
                                data={"token": provided_token, "tool": tool_name},
                            ),
                        ).model_dump()
                        await TraceService.record_trace(
                            session_id=session_id,
                            method=method,
                            tool_name=tool_name,
                            raw_arguments=arguments,
                            policy_decision="rejected_invalid_token",
                            matched_rule_id=eval_result.matched_rule_id,
                            policy_reason="Attempted execution with invalid approval token",
                            risk_level=eval_result.risk_level.value,
                            approval_id=None,
                            approval_status="invalid",
                            raw_result=None,
                            error=err_resp["error"]["message"],
                            duration_ms=duration_ms,
                            request_id=req_id,
                            simulated_tokens=estimated_tokens,
                            simulated_cost_usd=estimated_cost,
                            trace_id=trace_id,
                        )
                        return err_resp

                # No token provided -> pause execution and generate approval ticket
                appr_record = await ApprovalManager.create_approval(
                    trace_id=trace_id,
                    session_id=session_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    risk_level=eval_result.risk_level.value,
                    reason=eval_result.reason,
                )

                duration_ms = (time.perf_counter() - t_start) * 1000.0
                await TraceService.record_trace(
                    session_id=session_id,
                    method=method,
                    tool_name=tool_name,
                    raw_arguments=arguments,
                    policy_decision="require_approval",
                    matched_rule_id=eval_result.matched_rule_id,
                    policy_reason=eval_result.reason,
                    risk_level=eval_result.risk_level.value,
                    approval_id=appr_record.id,
                    approval_status="pending",
                    raw_result=None,
                    error=None,
                    duration_ms=duration_ms,
                    request_id=req_id,
                    simulated_tokens=estimated_tokens,
                    simulated_cost_usd=estimated_cost,
                    trace_id=trace_id,
                )

                # Return structured JSON-RPC error alerting agent that approval is pending
                return JsonRpcResponse(
                    id=req_id,
                    error=JsonRpcError(
                        code=-32001,
                        message=f"Human Approval Required: {eval_result.reason}",
                        data={
                            "approval_id": appr_record.id,
                            "approval_token": appr_record.token,
                            "tool": tool_name,
                            "risk_level": eval_result.risk_level.value,
                            "expires_at": appr_record.expires_at,
                            "trace_id": trace_id,
                            "resume_instruction": (
                                f"To resume after approval in web dashboard, re-invoke tools/call "
                                f"with '_approval_token': '{appr_record.token}'"
                            ),
                        },
                    ),
                ).model_dump()

            # Case C: Allowed by Policy
            return await self._execute_and_record(
                req_id=req_id,
                session_id=session_id,
                method=method,
                tool_name=tool_name,
                arguments=arguments,
                t_start=t_start,
                policy_decision="allow",
                matched_rule_id=eval_result.matched_rule_id,
                policy_reason=eval_result.reason,
                risk_level=eval_result.risk_level.value,
                approval_token=None,
                approval_status="none",
                estimated_tokens=estimated_tokens,
                estimated_cost=estimated_cost,
                trace_id=trace_id,
            )

        # 4. Any other method
        return JsonRpcResponse(
            id=req_id,
            error=JsonRpcError(code=-32601, message=f"Method '{method}' not supported by Relay proxy"),
        ).model_dump()

    async def _execute_and_record(
        self,
        req_id: str | int | None,
        session_id: str,
        method: str,
        tool_name: str,
        arguments: dict[str, Any],
        t_start: float,
        policy_decision: str,
        matched_rule_id: str | None,
        policy_reason: str | None,
        risk_level: str,
        approval_token: str | None,
        approval_status: str,
        estimated_tokens: int,
        estimated_cost: float,
        trace_id: str,
    ) -> dict[str, Any]:
        """Execute the tool under timeout guard and log sanitized trace record."""
        tool_result = None
        error_msg = None

        try:
            # Enforce hard execution timeout
            tool_result = await asyncio.wait_for(
                self.backend.execute_tool(tool_name, arguments),
                timeout=settings.tool_timeout_seconds,
            )
            # Record spend
            await policy_engine.record_session_spend(session_id, estimated_cost)
            resp = JsonRpcResponse(id=req_id, result=tool_result).model_dump()
        except asyncio.TimeoutError:
            error_msg = f"Execution timed out after {settings.tool_timeout_seconds}s limit"
            resp = JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(code=-32002, message=error_msg),
            ).model_dump()
        except Exception as exc:
            error_msg = str(exc)
            resp = JsonRpcResponse(
                id=req_id,
                error=JsonRpcError(code=-32603, message=f"Tool Execution Error: {error_msg}"),
            ).model_dump()

        duration_ms = (time.perf_counter() - t_start) * 1000.0

        await TraceService.record_trace(
            session_id=session_id,
            method=method,
            tool_name=tool_name,
            raw_arguments=arguments,
            policy_decision=policy_decision,
            matched_rule_id=matched_rule_id,
            policy_reason=policy_reason,
            risk_level=risk_level,
            approval_id=approval_token,
            approval_status=approval_status,
            raw_result=tool_result,
            error=error_msg,
            duration_ms=duration_ms,
            request_id=req_id,
            simulated_tokens=estimated_tokens,
            simulated_cost_usd=estimated_cost,
            trace_id=trace_id,
        )

        return resp


# Global proxy instance
proxy = McpProxy()
