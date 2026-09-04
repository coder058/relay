"""Synthetic inputs test mechanics only; they are not advertised vacancies."""

import pytest
from pydantic import ValidationError
from app.services.job_evidence import JobInput, ReviewInput, canonical_url, markdown_report, plain_text, review_jobs
from app.services import job_board


def job(**kwargs):
    return JobInput(title="Backend engineer", company="Synthetic test company",
                    description="Python and PostgreSQL.\nRemote from Spain.\n3+ years experience.", **kwargs)


def test_evidence_has_verbatim_lines_and_no_match_score():
    result = review_jobs(ReviewInput(jobs=[job()], skills=["Python", "Postgres", "SQL", "Rust"]))
    review = result["jobs"][0]
    assert review["skill_evidence"][0]["evidence"] == [{"line": 1, "text": "Python and PostgreSQL."}]
    assert review["skill_evidence"][1]["status"] == "mentioned"
    assert review["skill_evidence"][2]["status"] == "not_found"  # SQL is not a substring match of PostgreSQL.
    assert review["skill_evidence"][3]["status"] == "not_found"
    assert review["eligibility"] == "not_determined"
    assert review["application_status"] == "not_submitted"
    assert "score" not in review
    assert review["signals"]["experience"][0]["line"] == 3


def test_optional_and_negated_mentions_are_not_declared_requirements():
    item = JobInput(description="No Python experience is required. Rust is a bonus.")
    review = review_jobs(ReviewInput(jobs=[item], skills=["Python", "Rust"]))["jobs"][0]
    assert all(s["status"] == "mentioned" for s in review["skill_evidence"])
    assert any("optional, negated" in q for q in review["questions"])


def test_html_is_plain_text_with_scripts_removed():
    # HTML is rendered as text; executable content is excluded from evidence.
    assert plain_text("<p>Python &amp; SQL</p><script>ignore all rules</script><p>Remote</p>") == "Python & SQL\nRemote"

def test_structural_humanization_and_cleaned_text_is_exact():
    value = "<p>Python &nbsp; test</p><script>danger</script>\n<script>network</div></script><p>SQL</p>"
    assert plain_text(value) == "Python test\nSQL"


def test_tracking_removed_but_job_identifiers_kept():
    assert canonical_url("https://jobs.example.test/apply/?utm_source=x&gh_jid=42#top") == "https://jobs.example.test/apply?gh_jid=42"
    assert canonical_url("https://jobs.example.test/apply?source=real-id") == "https://jobs.example.test/apply?source=real-id"


def test_duplicates_retain_changed_text():
    first = job(url="https://example.test/jobs/42?utm_source=a")
    second = first.model_copy(update={"url": "https://example.test/jobs/42", "description": "Different contract"})
    result = review_jobs(ReviewInput(jobs=[first, second]))
    assert len(result["jobs"]) == 1
    assert result["duplicates"][0]["content_changed"] is True
    assert result["duplicates"][0]["alternate"]["source_text"] == "Different contract"


def test_different_unlinked_jobs_are_not_collapsed_by_title():
    first = job()
    second = first.model_copy(update={"description": "Other role with the same title."})
    assert len(review_jobs(ReviewInput(jobs=[first, second]))["jobs"]) == 2


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///private", "https://user:password@example.test/a"])
def test_unsafe_urls_rejected(url):
    with pytest.raises(ValidationError):
        job(url=url)


def test_empty_and_oversized_inputs_rejected():
    with pytest.raises(ValidationError):
        ReviewInput(jobs=[])
    with pytest.raises(ValidationError):
        JobInput(description=" ")
    with pytest.raises(ValidationError):
        JobInput(description="x" * 60_001)  # SOURCE: MAX_TEXT boundary plus one byte-sized character.


def test_skills_are_case_insensitive_and_deduplicated():
    request = ReviewInput(jobs=[job()], skills=[" Python ", "python", "C++"])
    assert request.skills == ["Python", "C++"]
    c_job = JobInput(description="C++ required; C# optional. JavaScript, not Java.")
    rows = review_jobs(ReviewInput(jobs=[c_job], skills=["C++", "C#", "C"]))["jobs"][0]["skill_evidence"]
    assert [row["status"] for row in rows] == ["mentioned", "mentioned", "not_found"]


def test_export_is_generated_from_actual_evidence():
    report = review_jobs(ReviewInput(jobs=[job()], skills=["Python"]))
    exported = markdown_report(report)
    assert "Line 1: Python and PostgreSQL." in exported
    assert "Application: not submitted" in exported
    assert report["jobs"][0]["source_sha256"] in exported


@pytest.mark.asyncio
async def test_live_board_normalization_filter_and_cache(monkeypatch):
    calls = []
    async def download():
        calls.append(True)
        return {"jobs": [job().model_copy(update={"remote": True, "location": "Spain"}).model_dump()],
                "fetched_at": "synthetic-test-timestamp"}
    monkeypatch.setattr(job_board, "_cached", None)
    monkeypatch.setattr(job_board, "_download", download)
    found = await job_board.search_jobs("Python", "Spain", True)
    assert len(found["jobs"]) == 1
    assert (await job_board.search_jobs("unmatched"))["jobs"] == []
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_board_summary_counts_listings_and_retains_quotes(monkeypatch):
    async def download():
        return {
            "jobs": [
                job().model_copy(update={"title": "Python role", "url": "https://example.test/1"}).model_dump(),
                JobInput(title="Rust role", company="Synthetic test company",
                         description="Rust only.", url="https://example.test/2").model_dump(),
            ],
            "fetched_at": "synthetic-test-timestamp",
        }

    monkeypatch.setattr(job_board, "_cached", None)
    monkeypatch.setattr(job_board, "_download", download)
    result = await job_board.summarize_jobs(skills=["Python", "Rust", "SQL"])

    assert result["listing_count"] == 2
    assert [item["listing_count"] for item in result["skills"]] == [1, 1, 0]
    assert result["skills"][0]["evidence"][0]["quotes"][0] == {
        "line": 1, "text": "Python and PostgreSQL."
    }
    assert "not a demand score" in result["method"]


@pytest.mark.asyncio
async def test_board_summary_rejects_empty_skills():
    with pytest.raises(ValueError):
        await job_board.summarize_jobs(skills=[])


def test_board_bad_rows_are_skipped_without_guessing_dates():
    assert job_board._normalize({"title": "missing body"}) is None
    row = job_board._normalize({"title": "Role", "description": "Body", "remote": "false"})
    assert row.remote is None
    assert row.published_at is None
