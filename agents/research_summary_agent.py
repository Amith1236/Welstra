"""Research summary agent - Generate human-readable investigation summary."""

from __future__ import annotations

from typing import Any

from models.schemas import ResumeData, RankedJobResult
from services.openai_clients import openai_client


class ResearchSummaryAgent:
    """Generate executive summary of job-finding investigation."""

    def __init__(self):
        self.client = openai_client

    async def run(
        self,
        resume_data: ResumeData,
        top_matches: list[RankedJobResult],
    ) -> tuple[str, dict[str, Any]]:
        """Generate summary of findings."""
        summary_text = self._build_summary(resume_data, top_matches)
        
        # Could use OpenAI to polish the summary, but keeping it simple for MVP
        return summary_text, {
            "source": "deterministic",
            "total_top_matches": len(top_matches),
        }

    @staticmethod
    def _build_summary(resume: ResumeData, top_matches: list[RankedJobResult]) -> str:
        """Build human-readable summary."""
        lines = []
        
        lines.append("## Job Finding Investigation Summary")
        lines.append("")
        lines.append(f"### Candidate Profile")
        lines.append(f"- **Name:** {resume.full_name}")
        lines.append(f"- **Current Role:** {resume.current_role or 'Not specified'}")
        lines.append(f"- **Experience:** {resume.years_experience} years")
        lines.append(f"- **Key Skills:** {', '.join(resume.skills[:5]) if resume.skills else 'None listed'}")
        lines.append("")
        
        if not top_matches:
            lines.append("### Finding")
            lines.append("No suitable job matches were found in the marketplace.")
            lines.append("")
            return "\n".join(lines)
        
        lines.append("### Top Opportunities")
        lines.append("")
        
        for result in top_matches[:5]:  # Show top 5
            lines.append(f"**Rank {result.rank}: {result.job_title}** at {result.company}")
            lines.append(f"- Match Score: {result.match_score:.0%}")
            lines.append(f"- Confidence: {result.confidence:.0%}")
            
            if result.key_reasons:
                lines.append(f"- Why this match: {', '.join(result.key_reasons[:3])}")
            
            lines.append(f"- [View Job]({result.job_url})")
            lines.append("")
        
        lines.append("### Recommendations")
        if top_matches:
            avg_score = sum(r.match_score for r in top_matches[:5]) / min(5, len(top_matches))
            
            if avg_score > 0.8:
                lines.append("Strong matches found! Consider applying to the top-ranked opportunities.")
            elif avg_score > 0.6:
                lines.append("Good matches available. The ranked jobs offer solid alignment with your background.")
            else:
                lines.append("Moderate matches available. Consider addressing any skill gaps mentioned.")
        
        lines.append("")
        lines.append("---")
        lines.append(f"*Summary generated for {resume.full_name}*")
        
        return "\n".join(lines)