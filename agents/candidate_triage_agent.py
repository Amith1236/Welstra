"""Candidate triage agent - Assess job fit for candidates."""

from __future__ import annotations

from typing import Any

from models.schemas import ResumeData, JobProduct, CandidateTriageAssessment
from services.openai_clients import openai_client
from services.settings import settings


class CandidateTriageAgent:
    """Triage job candidates to assess fit with candidate resume."""

    def __init__(self):
        self.client = openai_client

    async def run(
        self,
        resume_data: ResumeData,
        candidate_job: JobProduct,
    ) -> tuple[CandidateTriageAssessment, dict[str, Any]]:
        """Assess if job is suitable for candidate."""
        response = await self.client.triage_job_fit(
            resume_data.resume_text,
            candidate_job.job_description,
            candidate_job.job_title,
        )
        
        assessment = CandidateTriageAssessment(
            job_url=str(candidate_job.job_url),
            is_suitable=response.is_suitable,
            confidence_score=response.confidence_score,
            is_outdated=response.is_outdated,
            reason=response.reason,
            missing_skills=response.missing_skills,
            matching_skills=response.matching_skills,
        )
        
        return assessment, {
            "source": "openai",
            "model": settings.openai_triage_model,
            "is_suitable": response.is_suitable,
            "confidence_score": response.confidence_score,
        }
