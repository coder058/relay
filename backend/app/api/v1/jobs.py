"""Stateless job evidence API; never persist applicant or listing inputs."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from fastapi.responses import PlainTextResponse
from app.services.job_board import BoardUnavailable, MAX_QUERY_LENGTH, summarize_jobs, search_jobs
from app.services.job_evidence import MAX_SKILLS
from app.services.job_evidence import ReviewInput, markdown_report, review_jobs

router = APIRouter(prefix="/jobs", tags=["Job evidence"])


class SummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="", max_length=MAX_QUERY_LENGTH)
    location: str = Field(default="", max_length=MAX_QUERY_LENGTH)
    remote_only: bool = False
    skills: list[str] = Field(min_length=1, max_length=MAX_SKILLS)


@router.get("/search")
async def search(query: str = Query("", max_length=MAX_QUERY_LENGTH),
                 location: str = Query("", max_length=MAX_QUERY_LENGTH), remote_only: bool = False):
    try:
        return await search_jobs(query, location, remote_only)
    except BoardUnavailable as exc:
        # SOURCE: HTTP 503 denotes upstream temporary unavailability; do not return invented jobs.
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/summary")
async def summary(payload: SummaryRequest):
    try:
        return await summarize_jobs(payload.query, payload.location, payload.remote_only, payload.skills)
    except BoardUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/review")
async def review(payload: ReviewInput):
    return review_jobs(payload)


@router.post("/export", response_class=PlainTextResponse)
async def export(payload: ReviewInput):
    return PlainTextResponse(markdown_report(review_jobs(payload)), media_type="text/markdown",
                             headers={"Content-Disposition": 'attachment; filename="relay-review.md"',
                                      "Cache-Control": "no-store"})
