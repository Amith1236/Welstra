"""Welstra — FastAPI backend with full agent pipeline wired."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.evidence_agent import EvidenceAgent
from agents.evaluating_agent import EvaluatingAgent
from agents.ranking_agent import RankingAgent
from agents.research_summary_agent import ResearchSummaryAgent
from agents.telegram_bot_agent import TelegramBotAgent
from models.schemas import ChatMessage, JobItem, ResumeData
from services.setting import settings

app = FastAPI(title="Welstra", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ───────────────────────────────────────────────────
_investigations: dict[str, dict] = {}


# ── /upload ───────────────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    (upload_dir / f"{file_id}.pdf").write_bytes(await file.read())
    return {"file_id": file_id}


# ── /investigate ──────────────────────────────────────────────────────────────
class InvestigateRequest(BaseModel):
    resume_file_id: str
    target_job_title: str | None = None


@app.post("/investigate")
async def start_investigation(req: InvestigateRequest):
    investigation_id = str(uuid.uuid4())
    _investigations[investigation_id] = {
        "status": "running",
        "current_agent": "job_extraction",
        "resume_file_id": req.resume_file_id,
        "suitable_jobs": [],
        "candidate_jobs": [],
        "top_matches": [],
        "summary": None,
        "raw_agent_outputs": {},
    }
    asyncio.create_task(_run_pipeline(investigation_id, req.resume_file_id))
    return {"investigation_id": investigation_id}


async def _run_pipeline(investigation_id: str, file_id: str):
    inv = _investigations[investigation_id]

    try:
        # ── Step 1: JobExtractionAgent ────────────────────────────────────────
        inv["current_agent"] = "job_extraction"
        # TODO: resume, suitable_jobs = await JobExtractionAgent().run(pdf_path)
        await asyncio.sleep(1)
        resume: ResumeData = _stub_resume()
        suitable_jobs = _stub_suitable_jobs()
        inv["suitable_jobs"] = [j.model_dump() for j in suitable_jobs]

        # ── Step 2: CandidateDiscoveryAgent ───────────────────────────────────
        inv["current_agent"] = "candidate_discovery"
        # TODO: candidate_jobs = await CandidateDiscoveryAgent().run(suitable_jobs[0], links)
        await asyncio.sleep(1)
        candidate_jobs = _stub_candidate_jobs()
        inv["candidate_jobs"] = [j.model_dump() for j in candidate_jobs]

        # ── Step 3: CandidateTriageAgent ──────────────────────────────────────
        inv["current_agent"] = "candidate_triage"
        # TODO: triaged = await CandidateTriageAgent().run(resume, candidate_jobs)
        await asyncio.sleep(1)

        # ── Step 4: CandidateComparisonAgent ──────────────────────────────────
        inv["current_agent"] = "candidate_comparison"
        # TODO: comparisons = [CandidateComparisonAgent().run(resume, job) for job in candidate_jobs]
        await asyncio.sleep(1)
        comparisons = _stub_comparisons(candidate_jobs)

        # ── Step 5: EvidenceAgent ─────────────────────────────────────────────
        inv["current_agent"] = "evidence"
        job_items: list[JobItem] = EvidenceAgent().run(resume, comparisons)
        inv["raw_agent_outputs"]["evidence"] = {"item_count": len(job_items)}

        # ── Step 6: RankingAgent ──────────────────────────────────────────────
        inv["current_agent"] = "ranking"
        ranked = RankingAgent().run(comparisons, job_items)
        inv["top_matches"] = [r.model_dump() for r in ranked]

        # ── Step 7: ResearchSummaryAgent ──────────────────────────────────────
        inv["current_agent"] = "summary"
        inv["summary"] = await ResearchSummaryAgent().run(resume, ranked)

        # ── Optional: TelegramBotAgent (non-blocking) ─────────────────────────
        asyncio.create_task(
            TelegramBotAgent().run(
                resume=resume,
                job_items=job_items,
                investigation_id=investigation_id,
            )
        )

        inv["status"] = "completed"

    except Exception as exc:  # noqa: BLE001
        inv["status"] = "failed"
        inv["raw_agent_outputs"]["error"] = str(exc)
        raise


# ── /investigation/{id} ───────────────────────────────────────────────────────
@app.get("/investigation/{investigation_id}")
async def get_investigation(investigation_id: str):
    inv = _investigations.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    return {"investigation_id": investigation_id, **inv}


# ── /chat ─────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    messages: list[dict]
    job: dict | None = None


@app.post("/chat")
async def chat(req: ChatRequest):
    history = [ChatMessage(role=m["role"], content=m["content"]) for m in req.messages]
    try:
        job_item = JobItem(**req.job) if req.job else _stub_job_item()
    except Exception:
        job_item = _stub_job_item()

    resume = _stub_resume()  # TODO: persist resume in session and retrieve here
    reply = await EvaluatingAgent().run(resume, job_item, history)
    return {"response": reply.content}


# ── /telegram/subscribe ───────────────────────────────────────────────────────
class TelegramSubscribeRequest(BaseModel):
    chat_id: str


@app.post("/telegram/subscribe")
async def telegram_subscribe(req: TelegramSubscribeRequest):
    # TODO: persist chat_id keyed by session/investigation_id
    return {"status": "subscribed", "chat_id": req.chat_id}


# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Stubs — replace each block with the real upstream agent's output ──────────

def _stub_resume() -> ResumeData:
    return ResumeData(
        full_name="Jane Doe", email="jane@example.com",
        years_experience=4,
        skills=["Python", "React", "FastAPI", "PostgreSQL", "Docker"],
        current_role="Software Engineer",
        education=["BSc Computer Science"], certifications=[],
        work_history=[{"company": "Acme Corp", "role": "SWE", "location": "Singapore"}],
        resume_text="",
    )


def _stub_suitable_jobs():
    from models.schemas import JobLevel, SuitableJob
    return [SuitableJob(
        job_title="Software Engineer", job_level=JobLevel.MID,
        confidence=0.88, reasoning="Strong Python and React background.",
        required_skills=["Python", "React"], years_required=3,
    )]


def _stub_candidate_jobs():
    from datetime import datetime, timezone
    from models.schemas import CandidateJob, JobLevel
    return [CandidateJob(
        job_id="job-001", job_title="Software Engineer",
        company="Stripe", job_level=JobLevel.MID, location="Singapore",
        job_description="Build payments infrastructure with Python and React.",
        required_skills=["Python", "React", "PostgreSQL"],
        years_required=3, posted_date=datetime.now(timezone.utc),
        job_url="https://stripe.com/jobs/1",  # type: ignore[arg-type]
        source="linkedin",
    )]


def _stub_comparisons(candidate_jobs):
    from models.schemas import ComparisonResult, MatchScore
    return [ComparisonResult(
        job_url=job.job_url, candidate_job=job,
        match_scores=MatchScore(skill_match=0.85, experience_match=0.90, level_match=1.0, overall_score=0.88),
        red_flags=[], green_flags=["strong_skill_overlap", "level_exact_match"],
        overall_fit=0.88,
    ) for job in candidate_jobs]


def _stub_job_item() -> JobItem:
    from models.schemas import JobLevel
    return JobItem(
        job_name="Software Engineer", company="Unknown",
        confidence=0.5, job_level=JobLevel.MID,
        supporting_data={}, link_to_job="https://example.com",  # type: ignore[arg-type]
        red_flags=[], match_score=0.5,
    )