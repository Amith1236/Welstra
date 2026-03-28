"""Pydantic schemas for job matching."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class JobLevel(str, Enum):
    """Job experience level."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class ResumeData(BaseModel):
    """Extracted resume information."""
    full_name: str
    email: str
    phone: Optional[str] = None
    years_experience: int
    skills: list[str]
    current_role: Optional[str] = None
    education: list[str]
    certifications: list[str]
    work_history: list[dict]
    resume_text: str  # Raw text for AI analysis


class SuitableJob(BaseModel):
    """Job suitable for candidate."""
    job_title: str
    job_level: JobLevel
    confidence: float  # 0-1 score from OpenAI
    reasoning: str
    required_skills: list[str]
    years_required: int


class CandidateJob(BaseModel):
    """Job found on market."""
    job_id: str
    job_title: str
    company: str
    job_level: JobLevel
    location: str
    salary_range: Optional[tuple[float, float]] = None
    job_description: str
    required_skills: list[str]
    years_required: int
    posted_date: datetime
    job_url: HttpUrl
    source: str  # "indeed", "linkedin", etc


class CandidateTriageAssessment(BaseModel):
    """Triage assessment for candidate-job pair."""
    product_url: HttpUrl
    is_suitable: bool
    confidence_score: float  # 0-1
    is_outdated: bool
    reason: str
    missing_skills: list[str]
    matching_skills: list[str]


class MatchScore(BaseModel):
    """Detailed match scoring."""
    skill_match: float  # 0-1
    experience_match: float  # 0-1
    level_match: float  # 0-1
    overall_score: float  # 0-1


class ComparisonResult(BaseModel):
    """Comparison between resume and job."""
    job_url: HttpUrl
    candidate_job: CandidateJob
    match_scores: MatchScore
    red_flags: list[str]  # Warning signals (old job posting, salary mismatch, etc)
    green_flags: list[str]  # Positive signals
    overall_fit: float  # 0-1


class JobItem(BaseModel):
    """Job evidence item."""
    job_name: str
    company: str
    confidence: float
    job_level: JobLevel
    supporting_data: dict  # skill matches, reasoning, etc
    link_to_job: HttpUrl
    red_flags: list[str]
    match_score: float


class RankedJobResult(BaseModel):
    """Top ranked job result."""
    rank: int
    job_item: JobItem
    match_reason: str
    recommendation: str  # "Highly recommend", "Consider applying", etc




class InvestigationCreateRequest(BaseModel):
    """Request to create a job matching investigation."""
    resume_file_id: str  # File uploaded to server
    target_job_title: Optional[str] = None  # Optional override


class InvestigationResponse(BaseModel):
    """Investigation status and results."""
    investigation_id: str
    status: str  # "pending", "running", "completed", "failed"
    created_at: datetime = Field(default_factory=utc_now)
    current_agent: Optional[str] = None
    suitable_jobs: list[SuitableJob]
    candidate_jobs: list[CandidateJob]
    top_matches: list[RankedJobResult]
    summary: Optional[str] = None
    raw_agent_outputs: dict


class ChatMessage(BaseModel):
    """Chat message for job discussion."""
    role: str  # "user" or "assistant"
    content: str


class ChatConversationResponse(BaseModel):
    """Chat conversation about job application."""
    job_item: JobItem
    messages: list[ChatMessage]
    interview_tips: list[str]


class TelegramNotification(BaseModel):
    """Telegram notification payload."""
    user_id: str
    investigation_id: str
    top_jobs: list[JobItem]
    message_text: str