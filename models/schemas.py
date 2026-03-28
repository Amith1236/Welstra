"""Pydantic schemas for the job-finding research platform."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)

class InvestigationStatus(str, Enum):
    """Status of an investigation."""
    queued = "queued"
    running = "running"
    delayed = "delayed"
    completed = "completed"
    failed = "failed"


class TaskStatus(str, Enum):
    """Status of an agent task."""
    queued = "queued"
    running = "running"
    delayed = "delayed"
    completed = "completed"
    failed = "failed"


class JobLevel(str, Enum):
    """Job seniority levels."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class ResumeData(BaseModel):
    """Normalized resume/candidate profile information."""
    full_name: str
    email: str
    phone: Optional[str] = None
    years_experience: int
    
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    work_history: list[dict[str, Any]] = Field(default_factory=list)
    
    current_role: Optional[str] = None
    resume_text: str


class JobRecommendation(BaseModel):
    """Single job recommendation from resume analysis."""
    job_title: str
    job_level: JobLevel
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    required_skills: list[str]
    years_required: int


class JobProduct(BaseModel):
    """Structured representation of a job posting discovered from job boards."""
    job_url: HttpUrl | str
    job_title: str
    company: str
    location: str
    job_level: JobLevel
    salary_range: Optional[tuple[float, float]] = None
    job_description: str
    required_skills: list[str] = Field(default_factory=list)
    years_required: int
    posted_date: datetime
    discovery_queries: list[str] = Field(default_factory=list)





class CandidateTriageAssessment(BaseModel):
    """Triage assessment for a discovered job candidate."""
    job_url: HttpUrl | str
    is_suitable: bool
    confidence_score: float = Field(ge=0, le=1)
    is_outdated: bool
    reason: str
    missing_skills: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)


class FeatureScores(BaseModel):
    """
    Raw 0-1 score for each comparison feature.
    Produced by CandidateComparisonAgent.
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


class FeatureWeights(BaseModel):
    """
    Weights for each feature in the scoring algorithm.
    Values should sum to 1.0 for proper weighted average.
    """
    skill_overlap: float = 0.25
    experience_gap: float = 0.15
    title_similarity: float = 0.10
    level_match: float = 0.10
    education_match: float = 0.05
    certification_match: float = 0.05
    preferred_skill_bonus: float = 0.05
    location_match: float = 0.10
    recency_penalty: float = 0.10
    salary_fit: float = 0.05


class ComparisonResult(BaseModel):
    """Result from comparing resume to a job posting."""
    job_url: HttpUrl | str
    candidate_job: JobProduct
    
    feature_scores: FeatureScores
    match_score: float = Field(ge=0, le=1, description="Weighted composite score")
    
    red_flags: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)
    reason: str


class JobItem(BaseModel):
    """Evidence item linking resume data to job opportunity."""
    job_name: str
    job_url: HttpUrl | str
    confidence: float = Field(ge=0, le=1)
    supporting_data: list[str] = Field(default_factory=list)
    match_score: float = Field(ge=0, le=1)


class RankedJobResult(BaseModel):
    """Top-ranked job with reasoning."""
    rank: int
    job_url: HttpUrl | str
    job_title: str
    company: str
    match_score: float
    confidence: float
    key_reasons: list[str]


class AgentTaskState(BaseModel):
    """State tracking for an agent task in the pipeline."""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    status: TaskStatus = TaskStatus.queued
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    provider_run_id: str | None = None
    provider_status: str | None = None
    last_heartbeat_at: datetime | None = None
    last_progress_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ActivityLogEntry(BaseModel):
    """Activity log entry for investigation progress."""
    timestamp: datetime = Field(default_factory=utc_now)
    level: str = "info"
    agent_name: str
    message: str
    job_url: HttpUrl | str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigationReport(BaseModel):
    """Report for a single resume-job matching investigation."""
    resume_data: ResumeData
    top_matches: list[RankedJobResult] = Field(default_factory=list)
    summary: str = ""
    raw_agent_outputs: list[AgentTaskState] = Field(default_factory=list)
    error: str | None = None


class InvestigationCreateRequest(BaseModel):
    """Request to start a job-finding investigation."""
    resume_text: str
    job_search_keywords: list[str]
    job_marketplace_url: HttpUrl | str
    max_candidates_per_search: int = Field(default=5, ge=1, le=10)


class InvestigationResponse(BaseModel):
    """Response containing investigation status and results."""
    investigation_id: str
    status: InvestigationStatus
    current_agent: str | None = None  # Current agent being executed
    report: Optional[InvestigationReport] = None
    activity_log: list[ActivityLogEntry] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InvestigationListItem(BaseModel):
    """Compact item for listing investigations."""
    investigation_id: str
    status: InvestigationStatus
    resume_name: Optional[str] = None
    job_keywords: list[str]
    error: str | None = None
    created_at: datetime
    updated_at: datetime