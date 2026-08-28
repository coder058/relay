"""Bound memory use before parsing JSON; never log or persist review payloads."""

from starlette.responses import JSONResponse

# GUESS: UNCALIBRATED GUESS operational cap, not an MCP protocol requirement.
MAX_JOB_REQUEST_BYTES = 2_000_000


class JobPrivacyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not (scope["path"].startswith("/api/v1/jobs") or scope["path"].startswith("/tools")):
            return await self.app(scope, receive, send)
        chunks = []
        size = 0  # SOURCE: initial count before receiving any request bytes.
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > MAX_JOB_REQUEST_BYTES:
                return await JSONResponse({"detail": "Listing batch is too large."}, status_code=413,
                                          headers={"Cache-Control": "no-store"})(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                message["headers"].append((b"cache-control", b"no-store"))
            await send(message)

        await self.app(scope, replay, private_send)
