"""Job extraction agent - Extract suitable jobs from resume."""

from __future__ import annotations

from typing import Any

from models.schemas import ResumeData, JobRecommendation
from services.openai_clients import openai_client


class JobExtractionAgent:
    """Extract suitable jobs from resume using OpenAI."""

    def __init__(self):
        self.client = openai_client

    async def run(
        self,
        resume_data: ResumeData,
    ) -> tuple[list[JobRecommendation], dict[str, Any]]:
        """Extract suitable jobs from resume."""
        response = await self.client.extract_jobs_from_resume(resume_data.resume_text)
        
        jobs = [
            JobRecommendation(
                job_title=job.job_title,
                job_level=job.job_level,
                confidence=job.confidence,
                reasoning=job.reasoning,
                required_skills=job.required_skills,
                years_required=job.years_required,
            )
            for job in response.jobs
        ]
        
        return jobs, {
            "source": "openai",
            "model": "gpt-4o-mini",
            "job_count": len(jobs),
        }
