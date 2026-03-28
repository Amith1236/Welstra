"""FastAPI backend for JobMatcher - AI-powered job finding."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.schemas import (
    InvestigationCreateRequest,
    InvestigationResponse,
    InvestigationStatus,
    ResumeData,
    utc_now,
)
from services.job_orchestrator import JobOrchestrator
from services.logging_config import configure_logging
from services.settings import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

logger = configure_logging()

app = FastAPI(
    title="JobMatcher",
    version="0.1.0",
    description="AI-powered job matching platform with agent pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# In-memory storage for investigations (in production, use a database)
investigations_store: dict[str, InvestigationResponse] = {}
orchestrator = JobOrchestrator()


# Health Check
@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "openai_enabled": "true" if settings.openai_enabled else "false",
    }


# Config Endpoint
@app.get("/config")
async def config() -> dict:
    return {
        "max_file_size": settings.max_file_size,
        "openai_enabled": settings.openai_enabled,
        "log_path": settings.log_path,
    }


# Create Investigation
@app.post("/investigate")
async def investigate(
    payload: InvestigationCreateRequest,
    background_tasks: BackgroundTasks,
) -> InvestigationResponse:
    """Create and start a job matching investigation."""
    try:
        investigation_id = f"inv_{uuid4().hex[:12]}"
        logger.info(f"Investigation created: {investigation_id}")
        
        # Build resume data from request
        resume_data = ResumeData(
            full_name="Candidate",  # Could be parsed from resume_text
            email="candidate@example.com",
            years_experience=0,  # Would parse from resume
            resume_text=payload.resume_text,
        )
        
        # Create investigation response
        investigation = InvestigationResponse(
            investigation_id=investigation_id,
            status=InvestigationStatus.queued,
        )
        
        # Store it
        investigations_store[investigation_id] = investigation
        
        # Schedule orchestration in background
        background_tasks.add_task(
            _run_investigation,
            investigation_id,
            resume_data,
            payload.job_marketplace_url,
            payload.max_candidates_per_search,
        )
        
        return investigation
    except Exception as e:
        logger.error(f"Investigation creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def _run_investigation(
    investigation_id: str,
    resume_data: ResumeData,
    job_marketplace_url: str,
    max_candidates: int,
) -> None:
    """Background task to run the investigation."""
    try:
        result = await orchestrator.investigate(
            investigation_id,
            resume_data,
            job_marketplace_url,
            max_candidates_per_search=max_candidates,
        )
        investigations_store[investigation_id] = result
    except Exception as e:
        logger.error(f"Investigation {investigation_id} failed: {e}")
        if investigation_id in investigations_store:
            investigations_store[investigation_id].error = str(e)
            investigations_store[investigation_id].status = "failed"


# Get Investigation Status
@app.get("/investigation/{investigation_id}")
async def get_investigation(investigation_id: str) -> InvestigationResponse:
    """Get investigation status and results."""
    investigation = investigations_store.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return investigation


# List Investigations
@app.get("/investigations")
async def list_investigations() -> dict:
    """List all investigations."""
    items = [
        {
            "investigation_id": inv.investigation_id,
            "status": inv.status,
            "created_at": inv.created_at,
            "updated_at": inv.updated_at,
        }
        for inv in investigations_store.values()
    ]
    return {"investigations": items, "total": len(items)}


# Cancel Investigation
@app.delete("/investigation/{investigation_id}")
async def cancel_investigation(investigation_id: str) -> dict:
    """Cancel an investigation."""
    investigation = investigations_store.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    
    investigation.status = "cancelled"
    investigation.updated_at = utc_now()
    
    return {"status": "cancelled", "investigation_id": investigation_id}


def run() -> None:
    """Run the server."""
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )


if __name__ == "__main__":
    run()