"""Candidate discovery agent - Find job listings from marketplaces."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from adapters.job_discovery_adapter import TinyFishJobDiscoveryAdapter
from models.schemas import JobProduct, JobRecommendation
from services.tinyfish_client import TinyFishRun


class CandidateDiscoveryAgent:
    """Discover job candidates from job marketplaces using TinyFish."""

    DEFAULT_TOP_N = 5

    def __init__(self, adapter: TinyFishJobDiscoveryAdapter | None = None) -> None:
        self.adapter = adapter or TinyFishJobDiscoveryAdapter()

    async def run(
        self,
        job_recommendations: list[JobRecommendation],
        job_marketplace_url: str,
        top_n: int = DEFAULT_TOP_N,
        on_update: Callable[[TinyFishRun], Awaitable[None] | None] | None = None,
    ) -> tuple[list[JobProduct], list[dict[str, Any]]]:
        """Search for job candidates from marketplace."""
        # Build search queries from job recommendations
        search_queries = self._build_search_queries(job_recommendations)
        
        # Search for each query in parallel
        search_tasks = [
            self.adapter.search_jobs(
                job_marketplace_url,
                [query],
                job_level=job_recommendations[0].job_level.value if job_recommendations else None,
                top_n=top_n,
                on_update=on_update,
            )
            for query in search_queries
        ]
        
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Merge results, deduplicating by URL
        jobs_by_url: dict[str, JobProduct] = {}
        raw_outputs: list[dict[str, Any]] = []
        
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                continue
            jobs, raw_output = result
            raw_outputs.append({"search_query": query, **raw_output})
            for job in jobs:
                job_url = str(job.job_url)
                if job_url not in jobs_by_url:
                    jobs_by_url[job_url] = job
        
        return list(jobs_by_url.values()), raw_outputs

    async def run_for_query(
        self,
        search_keywords: list[str],
        job_marketplace_url: str,
        job_level: str | None = None,
        top_n: int = DEFAULT_TOP_N,
        on_update: Callable[[TinyFishRun], Awaitable[None] | None] | None = None,
    ) -> tuple[list[JobProduct], dict[str, Any]]:
        """Search for a single query."""
        return await self.adapter.search_jobs(
            job_marketplace_url,
            search_keywords,
            job_level=job_level,
            top_n=top_n,
            on_update=on_update,
        )

    async def resume_for_query(
        self,
        run_id: str,
        search_keywords: list[str],
        on_update: Callable[[TinyFishRun], Awaitable[None] | None] | None = None,
        started_at: datetime | None = None,
        last_progress_at: datetime | None = None,
    ) -> tuple[list[JobProduct], dict[str, Any]]:
        """Resume a previous job search."""
        return await self.adapter.resume_search_jobs(
            run_id,
            search_keywords,
            on_update=on_update,
            started_at=started_at,
            last_progress_at=last_progress_at,
        )

    @staticmethod
    def _build_search_queries(recommendations: list[JobRecommendation]) -> list[str]:
        """Build search queries from job recommendations."""
        queries: list[str] = []
        for rec in recommendations[:3]:  # Top 3 recommendations
            queries.append(rec.job_title)
            queries.append(f"{rec.job_title} {rec.job_level.value}")
        
        # Deduplicate
        return list(dict.fromkeys(queries))[:5]
