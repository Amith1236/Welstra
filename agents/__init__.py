"""Job-finding agents for Welstra."""

from agents.job_extraction_agent import JobExtractionAgent
from agents.candidate_discovery_agent import CandidateDiscoveryAgent
from agents.candidate_triage_agent import CandidateTriageAgent
from agents.candidate_comparison_agent import CandidateComparisonAgent
from agents.evidence_agent import EvidenceAgent
from agents.ranking_agent import RankingAgent
from agents.research_summary_agent import ResearchSummaryAgent
from services.settings import settings
from services.openai_clients import OpenAIClient
from models.schemas import ResumeData, SuitableJob, JobLevel

__all__ = [
    "JobExtractionAgent",
    "CandidateDiscoveryAgent",
    "CandidateTriageAgent",
    "CandidateComparisonAgent",
    "EvidenceAgent",
    "RankingAgent",
    "ResearchSummaryAgent",
]



class JobExtractionAgent:
    """Extract suitable jobs from resume using OpenAI."""
    
    def __init__(self, client: OpenAIClient | None = None) -> None:
        self.client = client or OpenAIClient()
    
    async def run(self, resume_data: ResumeData) -> tuple[list[SuitableJob], dict[str, Any]]:
        """Extract suitable jobs from resume."""
        if not settings.openai_enabled:
            return self._heuristic_extraction(resume_data)
        
        try:
            payload = await self.client.run_json(
                model=settings.openai_job_extraction_model,
                instructions=self._instructions(),
                input_text=self._prompt(resume_data),
                schema_name="job_extraction_assessment",
                schema=self._schema(),
                max_output_tokens=800,
            )
            
            jobs = []
            if isinstance(payload, dict) and "suitable_jobs" in payload:
                for job_data in payload["suitable_jobs"]:
                    job = SuitableJob(
                        job_title=job_data.get("job_title", ""),
                        job_level=JobLevel(job_data.get("job_level", "mid")),
                        confidence=float(job_data.get("confidence", 0.5)),
                        reasoning=job_data.get("reasoning", ""),
                        required_skills=job_data.get("required_skills", []),
                        years_required=int(job_data.get("years_required", 0)),
                    )
                    jobs.append(job)
            
            raw_output = {
                "status": "success",
                "jobs_extracted": len(jobs),
                "openai_response": payload,
            }
            return jobs, raw_output
        
        except Exception as e:
            return self._heuristic_extraction(resume_data)
    
    @staticmethod
    def _instructions() -> str:
        return (
            "You are a career advisor analyzing resumes. "
            "Extract 3-5 suitable job titles and career levels for this candidate based on their experience. "
            "Consider their years of experience, current role, skills, and education. "
            "Return a JSON array of suitable jobs with job_title, job_level (entry/mid/senior/lead/executive), "
            "confidence (0-1), reasoning, required_skills (list), and years_required (int)."
        )
    
    @staticmethod
    def _prompt(resume_data: ResumeData) -> str:
        return (
            f"Full Name: {resume_data.full_name}\n"
            f"Years of Experience: {resume_data.years_experience}\n"
            f"Current Role: {resume_data.current_role}\n"
            f"Skills: {', '.join(resume_data.skills)}\n"
            f"Education: {', '.join(resume_data.education)}\n"
            f"Certifications: {', '.join(resume_data.certifications)}\n\n"
            f"Resume Text:\n{resume_data.resume_text}\n\n"
            "Analyze this resume and extract the most suitable job titles and levels for this candidate."
        )
    
    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "suitable_jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "job_title": {"type": "string"},
                            "job_level": {"type": "string", "enum": ["entry", "mid", "senior", "lead", "executive"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "reasoning": {"type": "string"},
                            "required_skills": {"type": "array", "items": {"type": "string"}},
                            "years_required": {"type": "integer"},
                        },
                        "required": ["job_title", "job_level", "confidence", "reasoning", "required_skills", "years_required"],
                    },
                    "minItems": 1,
                    "maxItems": 5,
                }
            },
            "required": ["suitable_jobs"],
        }
    
    @staticmethod
    def _heuristic_extraction(resume_data: ResumeData) -> tuple[list[SuitableJob], dict]:
        """Fallback heuristic extraction."""
        jobs = []
        years = resume_data.years_experience
        
        # Determine job level based on years
        if years < 2:
            level = JobLevel.ENTRY
        elif years < 5:
            level = JobLevel.MID
        elif years < 10:
            level = JobLevel.SENIOR
        else:
            level = JobLevel.LEAD
        
        # Extract job title from current role or skills
        current = resume_data.current_role or "Software Engineer"
        
        # Create suitable jobs based on skills and experience
        if any(skill in ["Python", "JavaScript", "Java", "Go"] for skill in resume_data.skills):
            jobs.append(SuitableJob(
                job_title="Backend Engineer" if "Python" in resume_data.skills else "Software Engineer",
                job_level=level,
                confidence=0.85,
                reasoning=f"{years} years experience with relevant technical skills",
                required_skills=resume_data.skills[:5],
                years_required=max(1, years - 2),
            ))
        
        if any(skill in ["React", "Vue", "Angular"] for skill in resume_data.skills):
            jobs.append(SuitableJob(
                job_title="Frontend Engineer",
                job_level=level,
                confidence=0.8,
                reasoning="Frontend framework experience detected",
                required_skills=[s for s in resume_data.skills if s in ["React", "Vue", "Angular", "JavaScript", "TypeScript"]],
                years_required=max(1, years - 2),
            ))
        
        if any(skill in ["AWS", "Docker", "Kubernetes"] for skill in resume_data.skills):
            jobs.append(SuitableJob(
                job_title="DevOps Engineer",
                job_level=JobLevel.MID if years >= 3 else JobLevel.ENTRY,
                confidence=0.75,
                reasoning="DevOps/Cloud infrastructure skills present",
                required_skills=[s for s in resume_data.skills if s in ["AWS", "Docker", "Kubernetes", "CI/CD"]],
                years_required=max(1, years - 1),
            ))
        
        return jobs, {"status": "heuristic", "jobs_extracted": len(jobs)}