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

TARGET ROLE
-----------
Job title:   {job_title}
Company:     {company}
Level:       {job_level}
Location:    {location}
Required skills: {required_skills}
Match score: {match_score:.0%}
Matched skills:  {matched_skills}
Missing skills:  {missing_skills}
Red flags:       {red_flags}

INSTRUCTIONS
------------
- Answer interview prep questions using the candidate's real experience above.
- When suggesting answers, frame them using the candidate's actual skills and work history.
- Point out which missing skills to address and suggest how to mitigate gaps.
- Keep answers concise and practical — no fluff.
- If asked for a mock interview, play the interviewer role and ask one question at a time.
- Never invent experience the candidate does not have.
"""


class EvaluatingAgent:
    """Stateless interview prep chatbot. Call .run() with full history each turn."""

    def __init__(self, model: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.model  = model or os.getenv("OPENAI_CHATBOT_MODEL", "gpt-4o-mini")

    async def run(
        self,
        resume: ResumeData,
        job_item: JobItem,
        history: list[ChatMessage],
    ) -> ChatMessage:
        """
        Given conversation history, return the next assistant message.

        history should include all prior turns (role: user / assistant).
        The system prompt is rebuilt on every call so the grounding is
        always fresh — safe for single-session use.
        """
        system_prompt = self._build_system(resume, job_item)
        messages = [{"role": "system", "content": system_prompt}]
        messages += [{"role": m.role, "content": m.content} for m in history]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )

        reply = response.choices[0].message.content or ""
        return ChatMessage(role="assistant", content=reply.strip())

    @staticmethod
    def _build_system(resume: ResumeData, job_item: JobItem) -> str:
        sd = job_item.supporting_data
        return _SYSTEM_TEMPLATE.format(
            full_name        = resume.full_name,
            current_role     = resume.current_role or "Not specified",
            years_experience = resume.years_experience,
            skills           = ", ".join(resume.skills) or "None listed",
            education        = ", ".join(resume.education) or "None listed",
            certifications   = ", ".join(resume.certifications) or "None listed",
            job_title        = job_item.job_name,
            company          = job_item.company,
            job_level        = job_item.job_level.value,
            location         = sd.get("location", "Not specified"),
            required_skills  = ", ".join(sd.get("matched_skills", []) + sd.get("missing_skills", [])) or "Not listed",
            match_score      = job_item.match_score,
            matched_skills   = ", ".join(sd.get("matched_skills", [])) or "None",
            missing_skills   = ", ".join(sd.get("missing_skills", [])) or "None",
            red_flags        = ", ".join(job_item.red_flags) or "None",
        )