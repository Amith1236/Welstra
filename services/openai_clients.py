"""OpenAI integration."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from services.settings import settings


# Pydantic models for structured outputs
class JobRecommendation(BaseModel):
    """Single job recommendation from resume analysis."""
    job_title: str
    job_level: str
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    required_skills: list[str]
    years_required: int


class JobExtractionResponse(BaseModel):
    """Response from job extraction."""
    jobs: list[JobRecommendation]


class TriageResponse(BaseModel):
    """Response from job fit triage."""
    is_suitable: bool
    confidence_score: float = Field(ge=0, le=1)
    is_outdated: bool
    reason: str
    missing_skills: list[str]
    matching_skills: list[str]


class ComparisonResponse(BaseModel):
    """Response from resume-job comparison."""
    skill_match: float = Field(ge=0, le=1)
    experience_match: float = Field(ge=0, le=1)
    level_match: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    red_flags: list[str]
    green_flags: list[str]


class OpenAIClient:
    """OpenAI client for agent tasks."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    

    async def extract_jobs_from_resume(self, resume_text: str) -> JobExtractionResponse:
        """Extract suitable jobs from resume using OpenAI."""

        response = await self.client.responses.parse(
            model=settings.openai_job_extraction_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a career advisor analyzing resumes. "
                        "Extract 3-5 suitable job titles and levels for this candidate. "
                        "Return JSON with: job_title, job_level, confidence, reasoning, "
                        "required_skills, years_required"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this resume:\n\n{resume_text}",
                },
            ],
            text_format=JobExtractionResponse,
            temperature=0.7,
        )
        
        return response.output_parsed
    
    async def triage_job_fit(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
    ) -> TriageResponse:
        """Triage if job is suitable for candidate."""
        response = await self.client.responses.parse(
            model=settings.openai_triage_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a job matching expert. "
                        "Analyze if a candidate (based on resume) is suitable for a job. "
                        "Return JSON with: is_suitable, confidence_score (0-1), "
                        "is_outdated, reason, missing_skills, matching_skills"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Resume:\n{resume_text}\n\n"
                        f"Job Title: {job_title}\n"
                        f"Job Description:\n{job_description}"
                    ),
                },
            ],
            text_format=TriageResponse,
            temperature=0.5,
        )
        
        return response.output_parsed
    
    async def compare_resume_job(
        self,
        resume_text: str,
        job_description: str,
    ) -> ComparisonResponse:
        """Deep comparison between resume and job."""
        response = await self.client.responses.parse(
            model=settings.openai_comparison_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a detailed job analyzer. "
                        "Compare resume against job requirements. "
                        "Return JSON with: skill_match (0-1), experience_match (0-1), "
                        "level_match (0-1), overall_score (0-1), red_flags (array), "
                        "green_flags (array)"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Resume:\n{resume_text}\n\n"
                        f"Job Description:\n{job_description}"
                    ),
                },
            ],
            text_format=ComparisonResponse,
            temperature=0.5,
        )
        
        return response.output_parsed


openai_client = OpenAIClient()