# Welstra - AI-Powered Job Finding Platform

Welstra is an intelligent job-finding platform that uses a multi-agent pipeline to analyze resumes and recommend the most suitable job opportunities. It combines OpenAI for intelligent analysis with TinyFish for web automation to search job marketplaces.

## Architecture Overview

Welstra implements a 7-agent pipeline modeled after TinyDetective's architecture, adapted for job finding:

```
Resume Input
    ↓
1. JobExtractionAgent (OpenAI)
    ↓ [JobRecommendation: suitable roles + levels]
2. CandidateDiscoveryAgent (TinyFish)
    ↓ [JobProduct: list of jobs found on marketplaces]
3. CandidateTriageAgent (OpenAI)
    ↓ [CandidateTriageAssessment: is_suitable, confidence]
4. CandidateComparisonAgent (Algorithm)
    ↓ [ComparisonResult: match_score with feature breakdown]
5. EvidenceAgent (Logic)
    ↓ [JobItem: evidence items for ranking]
6. RankingAgent (Algorithm)
    ↓ [RankedJobResult: top 10 jobs with reasoning]
7. ResearchSummaryAgent (Template)
    ↓
Final Human-Readable Summary
```

## Project Structure

```
Welstra/
├── agents/                      # Agent implementations
│   ├── job_extraction_agent.py
│   ├── candidate_discovery_agent.py
│   ├── candidate_triage_agent.py
│   ├── candidate_comparison_agent.py
│   ├── evidence_agent.py
│   ├── ranking_agent.py
│   └── research_summary_agent.py
│
├── adapters/                    # External service adapters
│   ├── job_discovery_adapter.py    # TinyFish job search
│   ├── comparison_site_adapter.py
│   ├── job_listing_adapter.py
│   └── job_page_adapter.py
│
├── models/                      # Pydantic schemas
│   ├── schemas.py               # Core domain models
│   └── case_schemas.py          # Investigation case models
│
├── services/                    # Business logic & infrastructure
│   ├── job_orchestrator.py      # Main pipeline coordinator
│   ├── openai_clients.py        # OpenAI integration
│   ├── tinyfish_client.py       # TinyFish web automation
│   ├── settings.py              # Configuration
│   ├── logging_config.py        # Logging setup
│   └── tinyfish_runtime.py      # Async runtime
│
├── backend/                     # FastAPI application
│   ├── main.py                  # API endpoints
│   └── __main__.py
│
├── frontend/                    # Web UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── pyproject.toml              # Dependencies
├── .env.example                # Configuration template
└── README.md                   # This file
```

## Core Components

### 1. JobExtractionAgent
**Input:** ResumeData  
**Output:** List[JobRecommendation]  
**Technology:** OpenAI GPT-4o-mini

Analyzes resume text to identify suitable job titles and seniority levels. Uses structured output parsing for consistent results.

```python
from agents.job_extraction_agent import JobExtractionAgent
agent = JobExtractionAgent()
jobs, output = await agent.run(resume_data)
```

### 2. CandidateDiscoveryAgent  
**Input:** JobRecommendation[], marketplace URL  
**Output:** List[JobProduct]  
**Technology:** TinyFish web automation

Searches job marketplaces (Indeed, LinkedIn, etc) for job listings. Builds multiple search queries and deduplicates results.

```python
from agents.candidate_discovery_agent import CandidateDiscoveryAgent
agent = CandidateDiscoveryAgent()
jobs, output = await agent.run(recommendations, "https://indeed.com", top_n=5)
```

### 3. CandidateTriageAgent
**Input:** ResumeData + JobProduct  
**Output:** CandidateTriageAssessment  
**Technology:** OpenAI GPT-4o-mini

Quick assessment of whether a job is suitable for the candidate. Identifies missing/matching skills.

### 4. CandidateComparisonAgent
**Input:** ResumeData + JobProduct  
**Output:** ComparisonResult  
**Technology:** Custom heuristic algorithm (NO AI)

Computes detailed match scores across 10 features:
- Skill overlap (25%)
- Experience gap (15%)
- Title similarity (15%)
- Level match (10%)
- Education match (8%)
- Certification match (7%)
- Preferred skill bonus (6%)
- Location match (5%)
- Recency penalty (5%)
- Salary fit (4%)

### 5. EvidenceAgent
**Input:** ResumeData + List[ComparisonResult]  
**Output:** List[JobItem]  
**Technology:** Logic-based

Extracts human-readable evidence items from comparison results.

### 6. RankingAgent
**Input:** List[ComparisonResult] + List[JobItem]  
**Output:** List[RankedJobResult]  
**Technology:** Custom ranking algorithm

Final ranking combines:
- Match score (50%)
- Confidence from evidence (25%)
- Posting freshness (15%)
- Flag balance - green vs red (10%)

Returns top 10 results.

### 7. ResearchSummaryAgent
**Input:** ResumeData + List[RankedJobResult]  
**Output:** Markdown summary  
**Technology:** Template-based

Generates human-readable markdown summary of findings with recommendations.

## API Endpoints

### Start Investigation
```bash
POST /investigate
Content-Type: application/json

{
  "resume_text": "Full resume content...",
  "job_search_keywords": ["Senior Software Engineer", "Tech Lead"],
  "job_marketplace_url": "https://www.indeed.com/jobs?q=engineer",
  "max_candidates_per_search": 5
}

Response:
{
  "investigation_id": "inv_abc123def456",
  "status": "queued",
  "created_at": "2026-03-28T10:00:00Z",
  "updated_at": "2026-03-28T10:00:00Z"
}
```

### Check Status
```bash
GET /investigation/{investigation_id}

Response:
{
  "investigation_id": "inv_abc123def456",
  "status": "completed",
  "report": {
    "resume_data": {...},
    "top_matches": [
      {
        "rank": 1,
        "job_url": "https://...",
        "job_title": "Senior Developer",
        "company": "TechCorp",
        "match_score": 0.87,
        "confidence": 0.91,
        "key_reasons": ["strong_skill_match", "exceeds_experience_requirements"]
      }
    ],
    "summary": "# Job Finding Summary\n..."
  },
  "activity_log": [...]
}
```

### List Investigations
```bash
GET /investigations
```

### Cancel Investigation
```bash
DELETE /investigation/{investigation_id}
```

## Setup & Usage

### Prerequisites
- Python 3.10+
- OpenAI API key
- TinyFish API key (for marketplace search)

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
uv sync --dev

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Configuration (.env)
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_JOB_EXTRACTION_MODEL=gpt-4o-mini
OPENAI_TRIAGE_MODEL=gpt-4o-mini
OPENAI_COMPARISON_MODEL=gpt-4o-mini

# TinyFish
TINYFISH_API_KEY=...
TINYFISH_BASE_URL=https://agent.tinyfish.ai
TINYFISH_BROWSER_PROFILE=stealth

# Backend
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

### Running the Server
```bash
# Development
uv run python -m backend

# Or directly
uv run python backend/main.py

# Server will be available at http://127.0.0.1:8000
```

### Testing with cURL
```bash
# Health check
curl http://127.0.0.1:8000/health

# Start investigation
curl -X POST http://127.0.0.1:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "I am a software engineer with 8 years of experience...",
    "job_search_keywords": ["Senior Engineer", "Tech Lead"],
    "job_marketplace_url": "https://www.indeed.com/jobs?q=engineer",
    "max_candidates_per_search": 5
  }'

# Check status
curl http://127.0.0.1:8000/investigation/inv_abc123def456
```

## Key Design Decisions

### 1. No AI for Comparison
The CandidateComparisonAgent uses a custom algorithm instead of OpenAI because:
- Deterministic, reproducible results
- Cost efficiency
- Transparency in scoring
- Easier to tune and debug

### 2. Modular Agent Design
Each agent follows a consistent interface:
```python
async def run(...) -> tuple[Output, dict[str, Any]]:
    """Run agent and return (results, metadata)."""
```
This allows:
- Easy testing and mocking
- Clear data flow
- Simple resumption from failures

### 3. TinyFish for Web Automation
Used instead of direct API calls to:
- Handle JavaScript-heavy job sites
- Bypass anti-scraping measures  
- Simulate real browser behavior
- Get up-to-date listings

### 4. Activity Logging
All agents log their actions for:
- Debugging
- User feedback during async operations
- Audit trail

## Development Notes

### Adding a New Agent
1. Create `agents/new_agent.py`
2. Implement `async def run(...)` method
3. Return `(results, metadata_dict)`
4. Add to `JobOrchestrator.investigate()`
5. Update agent `__init__.py`

### Testing
```bash
# Run tests
uv run pytest tests/

# Test specific agent
uv run pytest tests/test_agents.py::test_job_extraction
```

### Extending Comparison Algorithm
Edit `CandidateComparisonAgent.WEIGHTS` to adjust feature importance:
```python
WEIGHTS = {
    "skill_overlap": 0.30,  # Increase skill importance
    "experience_gap": 0.10,  # Decrease experience importance
    ...  # Total must sum to 1.0
}
```

## Performance

- **JobExtractionAgent**: ~3-5 seconds (OpenAI)
- **CandidateDiscoveryAgent**: ~30-60 seconds (TinyFish web search)
- **CandidateTriageAgent**: ~2-3 seconds per job × N jobs
- **CandidateComparisonAgent**: ~0.1 seconds per job (algorithm)
- **EvidenceAgent**: ~0.05 seconds per job (logic)
- **RankingAgent**: ~0.1 seconds (algorithm)
- **ResearchSummaryAgent**: ~0.5 seconds (template)

**Total for 5-10 jobs**: ~2-5 minutes

## Troubleshooting

### "OPENAI_API_KEY not set"
Check `.env` file and ensure `OPENAI_API_KEY` is populated.

### "TinyFish run failed"
- Check `TINYFISH_API_KEY` in `.env`
- Verify marketplace URL is current and accessible
- Check `TINYFISH_RUN_HARD_TIMEOUT_SECONDS` if searches are timing out

### "No jobs found"
- Verify job marketplace URL is correct
- Check if marketplace requires authentication
- Check TinyFish logs for browser errors

## Architecture Lessons from TinyDetective

Welstra's architecture is inspired by TinyDetective's proven patterns:

| Aspect | TinyDetective | Welstra |
|--------|---------------|---------|
| Source analysis | Official product URLs | Job marketplace search |
| Candidate discovery | Marketplace search | Job board search |
| Triage | Product comparison | Job fit assessment |
| Ranking | Risk scoring | Match scoring |
| Summary | Counterfeit risk report | Job opportunity report |

Both use:
- Modular agent design
- OpenAI for semantic analysis
- TinyFish for web automation
- Custom algorithms for scoring
- Structured activity logging

## Future Enhancements

- [ ] Interview preparation chatbot
- [ ] Salary negotiation guidance
- [ ] Interview question prediction
- [ ] Cover letter generation
- [ ] Reference check automation
- [ ] Database persistence (SQLite/PostgreSQL)
- [ ] Multi-resume batch processing
- [ ] Job alert subscriptions
- [ ] LinkedIn profile sync
- [ ] Telegram notifications

## License

TBD

## Support

For issues or questions, please open an issue in the project repository.