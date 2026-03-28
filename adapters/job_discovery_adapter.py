"""TinyFish-backed job discovery adapter for finding job listings."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Optional

from models.schemas import JobProduct, JobLevel, ResumeData
from services.tinyfish_client import TinyFishClient, TinyFishRun


class TinyFishJobDiscoveryAdapter:
    """Discover job listings from job marketplaces using TinyFish."""

    def __init__(self, client: TinyFishClient | None = None) -> None:
        self.client = client or TinyFishClient()

    async def search_jobs(
        self,
        job_marketplace_url: str,
        search_keywords: list[str],
        job_level: Optional[str] = None,
        top_n: int = 5,
        on_update: Callable[[TinyFishRun], Awaitable[None] | None] | None = None,
    ) -> tuple[list[JobProduct], dict[str, Any]]:
        """Search for jobs on a job marketplace."""
        run = await self.client.run_json(
            job_marketplace_url,
            self._build_goal(job_marketplace_url, search_keywords, job_level, top_n),
            on_update=on_update,
        )
        return self._coerce_jobs(run, search_keywords), self._raw_output(run)

    async def resume_search_jobs(
        self,
        run_id: str,
        search_keywords: list[str],
        on_update: Callable[[TinyFishRun], Awaitable[None] | None] | None = None,
        started_at: datetime | None = None,
        last_progress_at: datetime | None = None,
    ) -> tuple[list[JobProduct], dict[str, Any]]:
        """Resume a previously started job search."""
        run = await self.client.wait_for_run(
            run_id,
            on_update=on_update,
            started_at=started_at,
            last_progress_at=last_progress_at,
        )
        return self._coerce_jobs(run, search_keywords), self._raw_output(run)

    @staticmethod
    def _build_goal(
        marketplace_url: str,
        search_keywords: list[str],
        job_level: Optional[str] = None,
        top_n: int = 5,
    ) -> str:
        level_hint = f" at {job_level} level" if job_level else ""
        keywords_str = ", ".join(search_keywords)
        return (
            f"Search for job listings{level_hint} on {marketplace_url} using these keywords: {keywords_str}. "
            f"Extract the top {top_n} relevant job postings. "
            "For each job, return valid JSON with: "
            '{"jobs": [{'
            '"job_url": "link to the job posting", '
            '"job_title": "exact job title from posting", '
            '"company": "company name", '
            '"location": "job location or remote", '
            '"job_level": "entry/mid/senior/lead/executive", '
            '"salary_range": [min, max] or null, '
            '"job_description": "key excerpts from job description", '
            '"required_skills": ["skill1", "skill2", ...], '
            '"years_required": number of years experience required or 0'
            "}]} "
            "Return ONLY valid JSON, no other text."
        )

    @staticmethod
    def _coerce_jobs(run: TinyFishRun, search_keywords: list[str]) -> list[JobProduct]:
        """Parse TinyFish result into JobProduct objects."""
        result = TinyFishJobDiscoveryAdapter._coerce_result_object(run)
        jobs = []
        for job_data in result.get("jobs", []):
            try:
                job = JobProduct(
                    job_url=job_data.get("job_url") or "",
                    job_title=job_data.get("job_title") or "Unknown",
                    company=job_data.get("company") or "Unknown",
                    location=job_data.get("location") or "Unknown",
                    job_level=_parse_job_level(job_data.get("job_level") or "entry"),
                    salary_range=job_data.get("salary_range"),
                    job_description=job_data.get("job_description") or "",
                    required_skills=job_data.get("required_skills") or [],
                    years_required=int(job_data.get("years_required") or 0),
                    posted_date=datetime.now(),  # TinyFish doesn't return this, so use now
                    discovery_queries=search_keywords,
                )
                jobs.append(job)
            except Exception:
                # Skip malformed job entries
                continue
        return jobs

    @staticmethod
    def _coerce_result_object(run: TinyFishRun) -> dict[str, Any]:
        """Extract and parse JSON result from TinyFish run."""
        result = run.result
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Job discovery result was not valid JSON: {result}") from exc
        raise ValueError(f"Unexpected TinyFish job discovery result: {result!r}")

    @staticmethod
    def _raw_output(run: TinyFishRun) -> dict[str, Any]:
        """Extract raw TinyFish run details."""
        return {
            "tinyfish_run_id": run.run_id,
            "tinyfish_status": run.status,
            "tinyfish_result": run.result,
            "tinyfish_elapsed_seconds": run.elapsed_seconds,
            "tinyfish_delayed": run.delayed,
            "tinyfish_last_heartbeat_at": run.last_heartbeat_at.isoformat() if run.last_heartbeat_at else None,
            "tinyfish_last_progress_at": run.last_progress_at.isoformat() if run.last_progress_at else None,
        }


def _parse_job_level(level_str: str) -> JobLevel:
    """Parse job level string to enum."""
    level_str = (level_str or "").lower().strip()
    for level in JobLevel:
        if level.value == level_str:
            return level
    return JobLevel.MID
