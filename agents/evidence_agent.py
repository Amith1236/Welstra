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