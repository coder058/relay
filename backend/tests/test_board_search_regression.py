"""SYNTHETIC regression cases from the recruiter-facing search audit."""
import pytest
from app.services import job_board
from app.services.job_evidence import JobInput


@pytest.mark.asyncio
async def test_synthetic_search_matches_skill_tokens_and_aliases_not_substrings(monkeypatch):
    descriptions = {
        "lab": "Chemical reactions and reactor maintenance.",
        "react": "Build React.js interfaces with PostgreSQL.",
        "mysql": "MySQL database maintenance.",
        "sql": "SQL queries and C++ development.",
    }

    async def download():
        return {"jobs": [JobInput(title=key, company="SYNTHETIC test company",
                    description=value).model_dump() for key, value in descriptions.items()],
                "fetched_at": "SYNTHETIC timestamp"}

    monkeypatch.setattr(job_board, "_cached", None)
    monkeypatch.setattr(job_board, "_download", download)
    async def titles(query):
        return [job["title"] for job in (await job_board.search_jobs(query))["jobs"]]
    assert await titles("React") == ["react"]
    assert await titles("SQL") == ["sql"]
    assert await titles("postgres") == ["react"]
    assert await titles("C++") == ["sql"]
    assert await titles("React PostgreSQL") == ["react"]
    assert await titles("React Python") == []
