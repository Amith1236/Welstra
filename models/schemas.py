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
    """Comparison between resume and job — output of CandidateComparisonAgent."""
    job_url: HttpUrl
    candidate_job: CandidateJob
 
    # Per-feature breakdown (0-1 each)
    feature_scores: FeatureScores
 
    # Weighted composite
    match_score: float  # 0-1
 
    # Signal lists
    red_flags: list[str]    # e.g. "overqualified", "salary_below_band", "stale_posting"
    green_flags: list[str]  # e.g. "strong_skill_overlap", "level_exact_match"
 
    # Human-readable explanation
    reason: str
 
## Feature score for comparison result
class FeatureWeights(BaseModel):
    """
    Weights for each comparison feature. All weights should sum to 1.0.
    Edit or zero-out any feature here to tune the algorithm.
    """
    skill_overlap: float = 0.25          # % of required skills the resume covers
    experience_gap: float = 0.15         # resume years vs job years_required
    title_similarity: float = 0.15       # word-overlap between resume role and job title
    level_match: float = 0.10           # JobLevel alignment (exact / adjacent / far)
    education_match: float = 0.08       # degree keywords vs job description
    certification_match: float = 0.07   # cert keywords in job description
    preferred_skill_bonus: float = 0.06  # % of *preferred* skills the resume covers
    location_match: float = 0.05        # remote / city match vs candidate location
    recency_penalty: float = 0.05       # posting age penalty (older = lower)
    salary_fit: float = 0.04            # resume inferred band vs job salary_range
 
 
class FeatureScores(BaseModel):
    """
    Raw 0-1 score for each feature produced by CandidateComparisonAgent.
    Each field mirrors a key in FeatureWeights.
    """
    skill_overlap: float = 0.0
    experience_gap: float = 0.0
    title_similarity: float = 0.0
    level_match: float = 0.0
    education_match: float = 0.0
    certification_match: float = 0.0
    preferred_skill_bonus: float = 0.0
    location_match: float = 0.0
    recency_penalty: float = 0.0
    salary_fit: float = 0.0

 
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