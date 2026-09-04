"""Read-only smoke check against a running MCP endpoint; never submits applications."""

import argparse
import asyncio
import json
from mcp import Client


async def verify(url: str, query: str = "Python"):
    # GUESS: UNCALIBRATED GUESS smoke-test deadline, including a cold start.
    async with Client(url, read_timeout_seconds=45) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        assert names == {
            "search_job_board", "summarize_job_board", "review_job_evidence", "export_job_review"
        }, names
        board = await client.call_tool("search_job_board", {"query": query})
        assert not board.is_error, board.content
        assert board.structured_content is not None
        jobs = board.structured_content["jobs"]
        # SOURCE: one real result suffices to test the workflow without sending a large batch.
        if not jobs:
            raise RuntimeError(f"No current result for {query!r}; do not replace it with invented data.")
        summary = await client.call_tool("summarize_job_board", {"query": query, "skills": [query]})
        assert not summary.is_error and summary.structured_content is not None
        assert summary.structured_content["listing_count"] == len(jobs)
        assert "not a demand score" in summary.structured_content["method"]
        payload = {"jobs": jobs[:1], "skills": ["Python"]}
        review = await client.call_tool("review_job_evidence", payload)
        assert not review.is_error and review.structured_content is not None
        evidence = review.structured_content["jobs"][0]
        assert evidence["application_status"] == "not_submitted"
        assert evidence["eligibility"] == "not_determined"
        exported = await client.call_tool("export_job_review", payload)
        assert not exported.is_error
        assert any("Application: not submitted" in getattr(block, "text", "") for block in exported.content)
        print(json.dumps({"endpoint": url, "query": query, "tools": sorted(names), "board_fetched_at": board.structured_content["fetched_at"],
                          "board_matches": board.structured_content["matching_count"],
                          "summary_listing_count": summary.structured_content["listing_count"],
                          "reviewed_title": evidence["title"],
                          "source_url": evidence["url"], "source_sha256": evidence["source_sha256"],
                          "markdown_export": "verified", "application_submitted": False}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="HTTP MCP endpoint of the running Relay service")
    parser.add_argument("--query", default="Python", help="Literal board search; not an eligibility filter")
    args = parser.parse_args()
    asyncio.run(verify(args.url, args.query))
