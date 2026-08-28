"""Evidence-backed job review; no model, applicant ranking, or sending side effects.

The canonical-URL approach is adapted from the author's codingjob/job_scout.py.
Unlike that private workspace, this module contains no applicant records or paths.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

# GUESS: UNCALIBRATED GUESS resource bounds for an interactive review, not hiring criteria.
MAX_TEXT = 60_000
MAX_SKILLS = 40
MAX_JOBS = 20
MAX_LABEL = 200


class JobInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="Untitled opportunity", max_length=MAX_LABEL)
    company: str = Field(default="Not supplied", max_length=MAX_LABEL)
    url: str = Field(default="", max_length=MAX_TEXT)
    description: str = Field(min_length=1, max_length=MAX_TEXT)
    source: str = Field(default="Pasted by user; not independently verified", max_length=MAX_LABEL)
    published_at: str | None = Field(default=None, max_length=MAX_LABEL)
    location: str = Field(default="Not supplied", max_length=MAX_LABEL)
    remote: bool | None = None

    @field_validator("description")
    @classmethod
    def readable_description(cls, value: str) -> str:
        if not plain_text(value):
            raise ValueError("The listing must contain readable text.")
        return value

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        if not value:
            return ""
        parts = urlsplit(value)
        if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
            raise ValueError("Use an HTTP(S) listing URL without embedded credentials.")
        return value


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    jobs: list[JobInput] = Field(min_length=1, max_length=MAX_JOBS)
    skills: list[str] = Field(default_factory=list, max_length=MAX_SKILLS)

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, values: list[str]) -> list[str]:
        result = []
        for value in values:
            value = value.strip()
            if not value or len(value) > MAX_LABEL:
                raise ValueError("Each skill must be a nonempty short label.")
            if value.casefold() not in {s.casefold() for s in result}:
                result.append(value)
        return result


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden.append(tag)
        if not self.hidden and tag in {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()
        if not self.hidden and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value: str) -> str:
    if re.search(r"</?(?:p|div|li|br|h[1-6]|script|style|span|strong|a)\b", value, re.I):
        parser = _TextParser()
        parser.feed(value)
        value = "".join(parser.parts)
    return "\n".join(" ".join(line.split()) for line in unescape(value).splitlines() if line.strip())


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value)
    # SOURCE: codingjob canonicalization; preserve semantic ids (gh_jid, jobId, etc.).
    tracking = {"fbclid", "gclid", "gh_src", "lever-source"}
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in tracking]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/",
                       urlencode(sorted(query)), ""))


# SOURCE: explicit spelling aliases, not a claim that related technologies are interchangeable.
ALIASES = {
    "javascript": ("javascript", "js"), "typescript": ("typescript", "ts"),
    "node.js": ("node.js", "nodejs", "node js"), "node": ("node.js", "nodejs", "node js"),
    "ruby on rails": ("ruby on rails", "rails"), "rails": ("ruby on rails", "rails"),
    "postgresql": ("postgresql", "postgres"), "postgres": ("postgresql", "postgres"),
    "react": ("react", "react.js", "reactjs"), "c#": ("c#", "c sharp"),
    "c++": ("c++",), "sql": ("sql",),
}


def _mentions(term: str, line: str) -> bool:
    spellings = ALIASES.get(term.casefold(), (term,))
    return any(re.search(r"(?<![\w+#])" + re.escape(s) + r"(?![\w+#])", line, re.I) for s in spellings)


def _evidence(lines: list[str], pattern: str) -> list[dict]:
    return [{"line": index, "text": line} for index, line in enumerate(lines, start=1)
            if re.search(pattern, line, re.I)]  # SOURCE: human-facing line numbers are one-based.


def review_job(job: JobInput, skills: list[str]) -> dict:
    body = plain_text(job.description)
    lines = body.splitlines()
    url = canonical_url(job.url)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    identity = url or f"{job.title.casefold()}|{job.company.casefold()}|{digest}"
    skill_evidence = []
    for skill in skills:
        evidence = [{"line": i, "text": line} for i, line in enumerate(lines, start=1) if _mentions(skill, line)]
        skill_evidence.append({"skill": skill, "status": "mentioned" if evidence else "not_found",
                               "evidence": evidence})

    # SOURCE: literal terms only. Their presence is not an eligibility or employment-type inference.
    signals = {
        "employment": _evidence(lines, r"\b(full[ -]?time|part[ -]?time|contract|freelanc\w*|internship|permanent|vollzeit|teilzeit|jornada|indefinid\w*)\b"),
        "location_and_remote": _evidence(lines, r"\b(remote|hybrid|on[ -]?site|relocat\w*|remot[oa]|h[ií]brid[oa]|presencial|home[ -]?office)\b"),
        "experience": _evidence(lines, r"\b(\d+\s*(?:\+|[–-]\s*\d+)?\s*(?:years?|a[nñ]os?|jahre)|senior|junior|entry[ -]level)\b"),
        "work_authorization": _evidence(lines, r"\b(visa|sponsor\w*|work (?:permit|authori[sz]ation)|right to work|permiso de trabajo)\b"),
        "compensation": _evidence(lines, r"[$€£]|\b(salary|compensation|salario|gehalt)\b"),
    }
    questions = [f"Confirm {name.replace('_', ' ')} on the employer's original listing."
                 for name, evidence in signals.items() if not evidence]
    questions.append("Check the original listing is still open; a board listing is not employer verification.")
    questions.append("Review quoted wording: a mention can be optional, negated, or a benefit, not a requirement.")
    return {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
        "title": job.title, "company": job.company, "url": url, "source": job.source,
        "published_at": job.published_at, "location": job.location, "remote": job.remote,
        "source_sha256": digest, "source_text": body, "skill_evidence": skill_evidence,
        "signals": signals, "questions": questions,
        "eligibility": "not_determined", "application_status": "not_submitted",
    }


def review_jobs(request: ReviewInput) -> dict:
    jobs, duplicates = [], []
    by_id = {}
    for job in request.jobs:
        review = review_job(job, request.skills)
        if review["id"] in by_id:
            original = by_id[review["id"]]
            duplicates.append({"id": review["id"], "title": review["title"],
                               "reason": "same_canonical_url" if review["url"] else "same_title_company_and_text",
                               "content_changed": original["source_sha256"] != review["source_sha256"],
                               "alternate": review})
        else:
            by_id[review["id"]] = review
            jobs.append(review)
    return {
        "reviewed_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs, "duplicates": duplicates,
        "method": "Deterministic text evidence; no LLM, match score, or hiring prediction.",
        "privacy": "Analysis is not stored by this service. Save/export it on your device if wanted.",
    }


def markdown_report(report: dict) -> str:
    # Markdown generated as plain text; callers must escape/sanitize before rendering HTML.
    def text(value):
        return str(value).replace("\r", " ").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")
    out = ["# Relay — Job evidence review", "", report["method"], "", f"Reviewed: {report['reviewed_at']}"]
    for job in report["jobs"]:
        out += ["", f"## {text(job['title'])} — {text(job['company'])}",
                f"Source: {text(job['source'])}", f"Original URL: {text(job['url']) or 'Not supplied'}",
                f"Source SHA-256: {job['source_sha256']}", "Eligibility: not determined. Application: not submitted."]
        for item in job["skill_evidence"]:
            out += ["", f"### {text(item['skill'])}: {item['status']}"]
            out += [f"- Line {e['line']}: {text(e['text'])}" for e in item["evidence"]]
        for signal, evidence in job["signals"].items():
            out += ["", f"### {signal.replace('_', ' ')}: quoted wording" if evidence else f"### {signal.replace('_', ' ')}: not found"]
            out += [f"- Line {e['line']}: {text(e['text'])}" for e in evidence]
        out += ["", "### Questions to verify", *[f"- {text(q)}" for q in job["questions"]]]
    out += ["", f"Duplicate records: {len(report['duplicates'])}. Alternate text is retained in the JSON export."]
    return "\n".join(out) + "\n"
