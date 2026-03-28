"""Evaluating agent — interview prep chatbot.

Input:  ResumeData + JobItem + list[ChatMessage] (conversation history)
Output: ChatMessage (the assistant's next reply)

Uses OpenAI chat completions with a system prompt that grounds the model
in the candidate's actual resume and the target job's requirements.
Call .run() once per user message, passing the full history each time
(stateless — the caller owns history).
"""

from __future__ import annotations

import os

from openai import AsyncOpenAI

from models.schemas import ChatMessage, JobItem, ResumeData

_SYSTEM_TEMPLATE = """\
You are an expert interview coach helping a candidate prepare for a specific job application.

CANDIDATE PROFILE
-----------------
Name:              {full_name}
Current role:      {current_role}
Years experience:  {years_experience}
Skills:            {skills}
Education:         {education}
Certifications:    {certifications}

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