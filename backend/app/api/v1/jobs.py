"""Stateless job evidence API; never persist applicant or listing inputs."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.services.job_board import BoardUnavailable, MAX_QUERY_LENGTH, search_jobs
from app.services.job_evidence import ReviewInput, markdown_report, review_jobs

router = APIRouter(prefix="/jobs", tags=["Job evidence"])


@router.get("/search")
async def search(query: str = Query("", max_length=MAX_QUERY_LENGTH),
                 location: str = Query("", max_length=MAX_QUERY_LENGTH), remote_only: bool = False):
    try:
        return await search_jobs(query, location, remote_only)
    except BoardUnavailable as exc:
        # SOURCE: HTTP 503 denotes upstream temporary unavailability; do not return invented jobs.
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/review")
async def review(payload: ReviewInput):
    return review_jobs(payload)


@router.post("/export", response_class=PlainTextResponse)
async def export(payload: ReviewInput):
    return PlainTextResponse(markdown_report(review_jobs(payload)), media_type="text/markdown",
                             headers={"Content-Disposition": 'attachment; filename="relay-review.md"',
                                      "Cache-Control": "no-store"})
