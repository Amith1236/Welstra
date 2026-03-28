"""Job orchestrator service for coordinating the job-finding pipeline."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from uuid import uuid4

from agents.job_extraction_agent import JobExtractionAgent
from agents.candidate_discovery_agent import CandidateDiscoveryAgent
from agents.candidate_triage_agent import CandidateTriageAgent
from agents.candidate_comparison_agent import CandidateComparisonAgent
from agents.evidence_agent import EvidenceAgent
from agents.ranking_agent import RankingAgent
from agents.research_summary_agent import ResearchSummaryAgent

from models.schemas import (
    ActivityLogEntry,
    AgentTaskState,
    InvestigationResponse,
    InvestigationStatus,
    ResumeData,
    TaskStatus,
    utc_now,
)

from services.logging_config import logger


class JobOrchestrator:
    """Coordinate the multi-agent job-finding workflow."""

    def __init__(
        self,
        job_extraction_agent: JobExtractionAgent | None = None,
        discovery_agent: CandidateDiscoveryAgent | None = None,
        triage_agent: CandidateTriageAgent | None = None,
        comparison_agent: CandidateComparisonAgent | None = None,
        evidence_agent: EvidenceAgent | None = None,
        ranking_agent: RankingAgent | None = None,
        summary_agent: ResearchSummaryAgent | None = None,
    ) -> None:
        self.job_extraction_agent = job_extraction_agent or JobExtractionAgent()
        self.discovery_agent = discovery_agent or CandidateDiscoveryAgent()
        self.triage_agent = triage_agent or CandidateTriageAgent()
        self.comparison_agent = comparison_agent or CandidateComparisonAgent()
        self.evidence_agent = evidence_agent or EvidenceAgent()
        self.ranking_agent = ranking_agent or RankingAgent()
        self.summary_agent = summary_agent or ResearchSummaryAgent()

    async def investigate(
        self,
        investigation_id: str,
        resume_data: ResumeData,
        job_marketplace_url: str,
        max_candidates_per_search: int = 5,
    ) -> InvestigationResponse:
        """Run the full investigation pipeline."""
        
        investigation = InvestigationResponse(
            investigation_id=investigation_id,
            status=InvestigationStatus.running,
        )
        
        try:
            # Step 1: Extract suitable jobs from resume
            logger.info(f"[{investigation_id}] Starting JobExtractionAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="JobExtractionAgent", message="Extracting suitable roles from resume")
            )
            
            job_recommendations, extraction_output = await self.job_extraction_agent.run(resume_data)
            logger.info(f"[{investigation_id}] JobExtractionAgent found {len(job_recommendations)} recommendations")
            
            # Step 2: Discover job candidates
            logger.info(f"[{investigation_id}] Starting CandidateDiscoveryAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="CandidateDiscoveryAgent", message="Searching for job listings...")
            )
            
            discovered_jobs, discovery_output = await self.discovery_agent.run(
                job_recommendations,
                job_marketplace_url,
                top_n=max_candidates_per_search,
            )
            logger.info(f"[{investigation_id}] CandidateDiscoveryAgent found {len(discovered_jobs)} jobs")
            
            if not discovered_jobs:
                investigation.status = InvestigationStatus.completed
                investigation.activity_log.append(
                    ActivityLogEntry(agent_name="JobOrchestrator", message="No jobs found matching criteria")
                )
                return investigation
            
            # Step 3: Triage candidates
            logger.info(f"[{investigation_id}] Starting CandidateTriageAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="CandidateTriageAgent", message="Assessing job fit...")
            )
            
            triaged_jobs = []
            for job in discovered_jobs:
                try:
                    triage_result, _ = await self.triage_agent.run(resume_data, job)
                    if triage_result.is_suitable:
                        triaged_jobs.append(job)
                except Exception as e:
                    logger.error(f"Triage error: {e}")
                    continue
            
            logger.info(f"[{investigation_id}] CandidateTriageAgent triaged {len(triaged_jobs)} suitable jobs")
            
            if not triaged_jobs:
                investigation.status = InvestigationStatus.completed
                investigation.activity_log.append(
                    ActivityLogEntry(agent_name="JobOrchestrator", message="No jobs passed triage")
                )
                return investigation
            
            # Step 4: Compare resume to jobs
            logger.info(f"[{investigation_id}] Starting CandidateComparisonAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="CandidateComparisonAgent", message="Comparing skills and experience...")
            )
            
            comparisons = []
            for job in triaged_jobs:
                try:
                    comparison_result, _ = await self.comparison_agent.run(resume_data, job)
                    comparisons.append(comparison_result)
                except Exception as e:
                    logger.error(f"Comparison error: {e}")
                    continue
            
            logger.info(f"[{investigation_id}] CandidateComparisonAgent processed {len(comparisons)} comparisons")
            
            # Step 5: Extract evidence
            logger.info(f"[{investigation_id}] Starting EvidenceAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="EvidenceAgent", message="Extracting supporting evidence...")
            )
            
            job_items, _ = await self.evidence_agent.run(resume_data, comparisons)
            logger.info(f"[{investigation_id}] EvidenceAgent created {len(job_items)} evidence items")
            
            # Step 6: Rank and select top matches
            logger.info(f"[{investigation_id}] Starting RankingAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="RankingAgent", message="Ranking top matches...")
            )
            
            top_matches, _ = await self.ranking_agent.run(comparisons, job_items)
            logger.info(f"[{investigation_id}] RankingAgent selected {len(top_matches)} top matches")
            
            # Step 7: Generate summary
            logger.info(f"[{investigation_id}] Starting ResearchSummaryAgent")
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="ResearchSummaryAgent", message="Generating summary...")
            )
            
            summary, _ = await self.summary_agent.run(resume_data, top_matches)
            logger.info(f"[{investigation_id}] ResearchSummaryAgent completed")
            
            # Build final report
            if investigation.report is None:
                from models.schemas import InvestigationReport
                investigation.report = InvestigationReport(
                    resume_data=resume_data,
                    top_matches=top_matches,
                    summary=summary,
                )
            else:
                investigation.report.top_matches = top_matches
                investigation.report.summary = summary
            
            investigation.status = InvestigationStatus.completed
            investigation.updated_at = utc_now()
            
            logger.info(f"[{investigation_id}] Investigation completed successfully")
            
        except Exception as e:
            logger.error(f"[{investigation_id}] Investigation failed: {e}")
            investigation.status = InvestigationStatus.failed
            investigation.error = str(e)
            investigation.activity_log.append(
                ActivityLogEntry(agent_name="JobOrchestrator", message=f"Error: {str(e)}", level="error")
            )
        
        investigation.updated_at = utc_now()
        return investigation
