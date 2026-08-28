"""Bounded read-only access to a fixed public board. Never fetch caller URLs."""

import asyncio
import json
import time
from datetime import datetime, timezone

import httpx

from app.services.job_evidence import JobInput, MAX_TEXT, plain_text

# SOURCE: Arbeitnow public job-board API, verified with a read-only request 2026-08-28.
BOARD_URL = "https://www.arbeitnow.com/api/job-board-api"
# GUESS: UNCALIBRATED GUESS operational limits; measure usage before changing them.
TIMEOUT_SECONDS = 12
MAX_RESPONSE_BYTES = 4_000_000
CACHE_SECONDS = 120
MAX_RESULTS = 30
MAX_QUERY_LENGTH = 100
_cached: dict | None = None
_cached_at = 0.0  # SOURCE: empty cache sentinel, not a measured timestamp.
_lock = asyncio.Lock()


class BoardUnavailable(Exception):
    pass


def _normalize(row: dict) -> JobInput | None:
    try:
        title = str(row.get("title") or "").strip()
        description = plain_text(str(row.get("description") or ""))
        if not title or not description or len(description) > MAX_TEXT:
            return None
        timestamp = row.get("created_at")
        published = None
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            published = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        return JobInput(title=title, company=str(row.get("company_name") or "Not supplied"),
                        url=str(row.get("url") or ""), description=description,
                        source="Arbeitnow public API — employer page not reverified", published_at=published,
                        location=str(row.get("location") or "Not supplied"),
                        remote=row.get("remote") if isinstance(row.get("remote"), bool) else None)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


async def _download() -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
            async with client.stream("GET", BOARD_URL, headers={"Accept": "application/json"}) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_RESPONSE_BYTES:
                        raise BoardUnavailable("The board response exceeded the safe size limit.")
        payload = json.loads(data)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise BoardUnavailable("The board returned an unexpected format.")
        return {"jobs": [job.model_dump() for row in payload["data"] if isinstance(row, dict)
                         if (job := _normalize(row)) is not None],
                "fetched_at": datetime.now(timezone.utc).isoformat()}
    except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BoardUnavailable("The public job board is unavailable. Paste a listing to continue.") from exc


async def search_jobs(query: str = "", location: str = "", remote_only: bool = False) -> dict:
    global _cached, _cached_at
    if len(query) > MAX_QUERY_LENGTH or len(location) > MAX_QUERY_LENGTH:
        raise ValueError("Search terms are too long.")
    async with _lock:
        if _cached is None or time.monotonic() - _cached_at >= CACHE_SECONDS:
            fresh = await _download()
            _cached, _cached_at = fresh, time.monotonic()
        snapshot = _cached
    terms = query.casefold().split()
    rows = [job for job in snapshot["jobs"]
            if all(term in f"{job['title']} {job['company']} {job['description']}".casefold() for term in terms)
            and location.casefold().strip() in job["location"].casefold()
            and (not remote_only or job["remote"] is True)]
    return {"jobs": rows[:MAX_RESULTS], "matching_count": len(rows), "scanned_count": len(snapshot["jobs"]),
            "fetched_at": snapshot["fetched_at"], "source_url": BOARD_URL,
            "coverage": "Searches the board's latest API page, not every opening or the private codingjob store.",
            "privacy": "Your search is filtered in service memory, not sent to the board. No application is submitted."}
