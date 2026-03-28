"""Research summary agent.

Input:  ResumeData + list[RankedJobResult]
Output: str (human-readable Markdown summary)

Produces a concise, structured summary of the job matching investigation.
Uses OpenAI to write the final prose; all data is passed deterministically
so the output is grounded in real scores — no hallucination risk.
"""

from __future__ import annotations

import os

from openai import AsyncOpenAI

from models.schemas import RankedJobResult, ResumeData

_PROMPT_TEMPLATE = """\
You are a career advisor writing a job search summary report for a candidate.

CANDIDATE
---------
Name:             {full_name}
Current role:     {current_role}
Years experience: {years_experience}
Skills:           {skills}

TOP JOB MATCHES (ranked)
------------------------
{matches_block}

TASK
----
Write a concise, honest 3–4 sentence summary that:
1. Identifies the candidate's strongest positioning (what makes them competitive).
2. Calls out the top 2–3 matched roles by name and why they fit.
3. Flags any common gaps or red flags across the matches.
4. Ends with one actionable next step.

Tone: direct, professional, encouraging but realistic.
Format: plain prose only — no bullet points, no headers, no markdown.
"""


def _matches_block(results: list[RankedJobResult]) -> str:
    lines: list[str] = []
    for r in results[:10]:
        ji = r.job_item
        lines.append(
            f"{r.rank}. {ji.job_name} @ {ji.company} — "
            f"match {ji.match_score:.0%}, confidence {ji.confidence:.0%} — "
            f"{r.recommendation} — {r.match_reason}"
        )
    return "\n".join(lines)


class ResearchSummaryAgent:
    """Generate a plain-text investigation summary from ranked results."""

    def __init__(self, model: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.model  = model or os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")

    async def run(
        self,
        resume: ResumeData,
        ranked_results: list[RankedJobResult],
    ) -> str:
        """Return a human-readable summary string."""
        if not ranked_results:
            return (
                f"No strong matches were found for {resume.full_name} "
                "in this search. Try broadening the target role or job boards."
            )

        prompt = _PROMPT_TEMPLATE.format(
            full_name        = resume.full_name,
            current_role     = resume.current_role or "Not specified",
            years_experience = resume.years_experience,
            skills           = ", ".join(resume.skills[:15]),  # cap for prompt length
            matches_block    = _matches_block(ranked_results),
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5,
        )

        return (response.choices[0].message.content or "").strip()