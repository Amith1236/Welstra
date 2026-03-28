"""FastAPI backend for JobMatcher - AI-powered job finding."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

# Mount frontend static files and SPA fallback
if FRONTEND_DIR.exists():
    # Build directory (created after 'npm run build')
    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.exists():
        app.mount("/static", StaticFiles(directory=dist_dir / "assets", html=False), name="static")
    else:
        # Fallback to source files for development
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=False), name="static")


# Catch-all route to serve index.html for SPA routing
@app.get("/")
async def root():
    """Serve frontend root page."""
    frontend_index = FRONTEND_DIR / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    # Fallback if index.html not found
    return {"message": "Frontend not found. Run 'npm run build' in /frontend directory."}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA files - fallback to index.html for client-side routing."""
    # Skip API routes
    if full_path.startswith("api") or full_path.startswith("health") or full_path.startswith("config") or full_path.startswith("investigate") or full_path.startswith("investigation") or full_path.startswith("investigations"):
        return None  # Let FastAPI handle API routes
    
    frontend_index = FRONTEND_DIR / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    raise HTTPException(status_code=404, detail="SPA not found")

# In-memory storage for investigations (in production, use a database)
investigations_store: dict[str, InvestigationResponse] = {}
uploaded_resumes: dict[str, str] = {}  # Store uploaded resume content by file_id
orchestrator = JobOrchestrator()


# File Upload
@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload and store resume file."""
    try:
        # Read file content
        content = await file.read()
        resume_text = content.decode('utf-8', errors='ignore')
        
        # Generate file ID and store
        file_id = f"file_{uuid4().hex[:12]}"
        uploaded_resumes[file_id] = resume_text
        
        logger.info(f"Resume uploaded: {file_id} ({len(resume_text)} characters)")
        return {"file_id": file_id}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


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
    payload: InvestigationCreateRequest | dict,
    background_tasks: BackgroundTasks,
) -> InvestigationResponse:
    """Create and start a job matching investigation."""
    try:
        # Handle both structured and dict payloads
        if isinstance(payload, dict):
            # Convert dict to proper request if it has file_id
            if "resume_file_id" in payload:
                file_id = payload.get("resume_file_id")
                if file_id not in uploaded_resumes:
                    raise HTTPException(status_code=404, detail=f"Resume {file_id} not found")
                resume_text = uploaded_resumes[file_id]
                payload = InvestigationCreateRequest(
                    resume_text=resume_text,
                    job_search_keywords=payload.get("job_search_keywords", ["software engineer"]),
                    job_marketplace_url=payload.get("job_marketplace_url", "https://example.com"),
                    max_candidates_per_search=payload.get("max_candidates_per_search", 5),
                )
            else:
                payload = InvestigationCreateRequest(**payload)
        
        investigation_id = f"inv_{uuid4().hex[:12]}"
        logger.info(f"Investigation created: {investigation_id}")
        
        # Build resume data from request
        resume_data = ResumeData(
            full_name="Candidate",
            email="candidate@example.com",
            years_experience=0,
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
            str(payload.job_marketplace_url),
            payload.max_candidates_per_search,
        )
        
        return investigation
    except HTTPException:
        raise
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