"""Evidence agent - Convert comparison results to structured evidence items."""

from __future__ import annotations

from typing import Any

from models.schemas import (
    ResumeData,
    ComparisonResult,
    JobItem,
)


class EvidenceAgent:
    """Extract evidence items from comparison results."""

    async def run(
        self,
        resume_data: ResumeData,
        comparison_results: list[ComparisonResult],
    ) -> tuple[list[JobItem], dict[str, Any]]:
        """Extract evidence from comparisons."""
        job_items = [
            self._create_job_item(resume_data, result)
            for result in comparison_results
        ]
        
        return job_items, {
            "total_comparisons": len(comparison_results),
            "evidence_items_created": len(job_items),
        }

    @staticmethod
    def _create_job_item(resume: ResumeData, result: ComparisonResult) -> JobItem:
        """Create evidence item from comparison result."""
        # Calculate confidence from match score and flag balance
        flag_adjustment = (len(result.green_flags) * 0.03) - (len(result.red_flags) * 0.04)
        confidence = min(1.0, max(0.0, result.match_score + flag_adjustment))
        
        # Build supporting data
        supporting_data = []
        
        if result.green_flags:
            supporting_data.append(f"Strengths: {', '.join(result.green_flags[:2])}")
        
        if result.red_flags:
            supporting_data.append(f"Concerns: {', '.join(result.red_flags[:2])}")
        
        # Add skill-related evidence
        if result.feature_scores.skill_overlap > 0.5:
            supporting_data.append(f"Good skill alignment ({result.feature_scores.skill_overlap:.0%})")
        
        if result.feature_scores.experience_gap > 0.8:
            supporting_data.append("Experience level acceptable or exceeds requirements")
        
        return JobItem(
            job_name=result.candidate_job.job_title,
            job_url=str(result.candidate_job.job_url),
            confidence=confidence,
            supporting_data=supporting_data,
            match_score=result.match_score,
        )

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