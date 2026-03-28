"""Evidence agent.

Input:  ResumeData + list[ComparisonResult]
Output: list[JobItem]

Converts raw comparison scores into structured, human-readable evidence
items that downstream agents (RankingAgent, EvaluatingAgent) can consume.
No AI calls — pure deterministic extraction from ComparisonResult.
"""

from __future__ import annotations

from datetime import datetime, timezone

from models.schemas import (
    ComparisonResult,
    JobItem,
    JobLevel,
    ResumeData,
)

# Confidence is derived from overall_fit + green/red flag balance.
# These weights tune how much flags adjust the raw score.
GREEN_FLAG_BONUS = 0.03   # per green flag (capped)
RED_FLAG_PENALTY = 0.04   # per red flag (capped)
MAX_FLAG_ADJUSTMENT = 0.15


def _days_since(dt: datetime) -> int:
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


class EvidenceAgent:
    """Build a JobItem evidence record for each ComparisonResult."""

    def run(
        self,
        resume: ResumeData,
        comparisons: list[ComparisonResult],
    ) -> list[JobItem]:
        """
        Process all ComparisonResults and return a JobItem per result.
        Results with overall_fit == 0.0 and no green flags are excluded.
        """
        items: list[JobItem] = []
        for comp in comparisons:
            item = self._build_item(resume, comp)
            if item is not None:
                items.append(item)
        return items

    def _build_item(
        self,
        resume: ResumeData,
        comp: ComparisonResult,
    ) -> JobItem | None:
        job = comp.candidate_job

        # Compute confidence from overall_fit adjusted by flags
        green_boost = min(MAX_FLAG_ADJUSTMENT, len(comp.green_flags) * GREEN_FLAG_BONUS)
        red_drag   = min(MAX_FLAG_ADJUSTMENT, len(comp.red_flags)   * RED_FLAG_PENALTY)
        confidence = round(min(1.0, max(0.0, comp.overall_fit + green_boost - red_drag)), 3)

        # Skip completely irrelevant results
        if confidence == 0.0 and not comp.green_flags:
            return None

        # Skill intersection evidence
        resume_skills_norm = {s.lower().strip() for s in resume.skills}
        matched_skills = [
            s for s in job.required_skills
            if s.lower().strip() in resume_skills_norm
        ]
        missing_skills = [
            s for s in job.required_skills
            if s.lower().strip() not in resume_skills_norm
        ]

        supporting_data = {
            # Skill evidence
            "matched_skills":    matched_skills,
            "missing_skills":    missing_skills,
            "skill_coverage":    round(
                len(matched_skills) / len(job.required_skills), 2
            ) if job.required_skills else 1.0,

            # Experience evidence
            "candidate_years":   resume.years_experience,
            "required_years":    job.years_required,
            "experience_delta":  resume.years_experience - job.years_required,

            # Score breakdown (from MatchScore)
            "score_breakdown": {
                "skill_match":       comp.match_scores.skill_match,
                "experience_match":  comp.match_scores.experience_match,
                "level_match":       comp.match_scores.level_match,
                "overall_score":     comp.match_scores.overall_score,
            },

            # Posting freshness
            "posting_age_days":  _days_since(job.posted_date),
            "source":            job.source,
            "location":          job.location,
            "salary_range":      list(job.salary_range) if job.salary_range else None,

            # Flags summary
            "green_flags":  comp.green_flags,
            "red_flags":    comp.red_flags,
        }

        return JobItem(
            job_name=job.job_title,
            company=job.company,
            confidence=confidence,
            job_level=job.job_level,
            supporting_data=supporting_data,
            link_to_job=comp.job_url,
            red_flags=comp.red_flags,
            match_score=comp.overall_fit,
        )