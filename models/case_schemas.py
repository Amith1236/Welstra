"""Additional Pydantic schemas for job-finding case management."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl

from models.schemas import (
    ActivityLogEntry,
    AgentTaskState,
    ComparisonResult,
    JobProduct,
    ResumeData,
    RankedJobResult,
    utc_now,
)


class JobSourceType(str, Enum):
    """Type of job source/marketplace."""
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASS_DOOR = "glassdoor"
    MONSTER = "monster"
    OTHER = "other"


class JobSearchQuery(BaseModel):
    """Prepared search query for job discovery."""
    keywords: list[str]
    job_level: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


class DiscoveredJobListing(BaseModel):
    """A job discovered during candidate discovery phase."""
    job_url: HttpUrl | str
    job_title: str
    company: str
    location: str
    posted_date: datetime
    discovery_source: JobSourceType
    discovery_query_keywords: list[str] = Field(default_factory=list)


class JobEvidence(BaseModel):
    """Evidence supporting job suitability."""
    category: str  # "skill_match", "experience", "title_match", "education", etc.
    evidence_text: str
    supporting_value: Optional[str | float] = None
    confidence: float = Field(ge=0, le=1)


class DetailedJobMatch(BaseModel):
    """Detailed match result with supporting evidence."""
    job_product: JobProduct
    comparison_result: ComparisonResult
    evidence_items: list[JobEvidence] = Field(default_factory=list)


class JobInvestigationCase(BaseModel):
    """Top-level case for a job-finding investigation."""
    case_id: str = Field(default_factory=lambda: f"case_{uuid4().hex[:8]}")
    resume_data: ResumeData
    search_query: JobSearchQuery
    investigation_start_time: datetime = Field(default_factory=utc_now)
    
    # Results at different stages
    initial_job_recommendations: list[str] = Field(default_factory=list)
    discovered_candidates: list[DiscoveredJobListing] = Field(default_factory=list)
    triaged_candidates: dict[str, bool] = Field(default_factory=dict)
    ranked_results: list[RankedJobResult] = Field(default_factory=list)
    
    final_summary: Optional[str] = None
    agent_logs: list[AgentTaskState] = Field(default_factory=list)
    activity_log: list[ActivityLogEntry] = Field(default_factory=list)

