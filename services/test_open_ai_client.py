"""Real integration test for OpenAIClient using assert checks."""

import asyncio
from openai_clients import OpenAIClient, JobExtractionResponse, TriageResponse, ComparisonResponse

# Sample resume and job description
SAMPLE_RESUME = """
John Smith
Senior Software Engineer
john.smith@email.com | (555) 123-4567

SUMMARY
Experienced Senior Software Engineer with 8+ years developing scalable web applications.
Expert in Python, JavaScript, and cloud technologies.
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Backend Engineer - Python

Requirements:
- 7+ years of backend development experience
- Expert in Python and FastAPI/Django
"""

async def run_real_tests():
    client = OpenAIClient()

    # -------------------------------
    # Test: extract_jobs_from_resume
    # -------------------------------
    print("=== Testing job extraction from resume ===")
    extraction_result: JobExtractionResponse = await client.extract_jobs_from_resume(SAMPLE_RESUME)
    print(extraction_result)

    # Basic assertions
    assert isinstance(extraction_result, JobExtractionResponse)
    assert len(extraction_result.jobs) > 0
    for job in extraction_result.jobs:
        assert 0 <= job.confidence <= 1
        assert job.job_title != ""
        assert job.job_level != ""
        assert isinstance(job.required_skills, list)
        assert job.years_required >= 0

    # -------------------------------
    # Test: triage_job_fit
    # -------------------------------
    print("\n=== Testing triage of job fit ===")
    triage_result: TriageResponse = await client.triage_job_fit(
        resume_text=SAMPLE_RESUME,
        job_description=SAMPLE_JOB_DESCRIPTION,
        job_title="Senior Backend Engineer - Python"
    )
    print(triage_result)

    assert isinstance(triage_result, TriageResponse)
    assert 0 <= triage_result.confidence_score <= 1
    assert isinstance(triage_result.is_suitable, bool)
    assert isinstance(triage_result.missing_skills, list)
    assert isinstance(triage_result.matching_skills, list)

    # -------------------------------
    # Test: compare_resume_job
    # -------------------------------
    print("\n=== Testing resume-job comparison ===")
    comparison_result: ComparisonResponse = await client.compare_resume_job(
        resume_text=SAMPLE_RESUME,
        job_description=SAMPLE_JOB_DESCRIPTION
    )
    print(comparison_result)

    assert isinstance(comparison_result, ComparisonResponse)
    assert 0 <= comparison_result.skill_match <= 1
    assert 0 <= comparison_result.experience_match <= 1
    assert 0 <= comparison_result.level_match <= 1
    assert 0 <= comparison_result.overall_score <= 1
    assert isinstance(comparison_result.red_flags, list)
    assert isinstance(comparison_result.green_flags, list)

if __name__ == "__main__":
    asyncio.run(run_real_tests())

"""
=== Testing job extraction from resume ===
jobs=[JobRecommendation(job_title='Lead Software Engineer', job_level='Senior', confidence=0.85, reasoning='The candidate has over 8 years of experience, indicating readiness for a leadership role.', required_skills=['Python', 'JavaScript', 'cloud technologies', 'team leadership'], years_required=5), JobRecommendation(job_title='Software Development Manager', job_level='Management', confidence=0.75, reasoning='The extensive experience in software engineering suggests potential for managerial responsibilities.', required_skills=['project management', 'team coordination', 'Python', 'JavaScript'], years_required=5), JobRecommendation(job_title='Senior Backend Developer', job_level='Senior', confidence=0.9, reasoning='Direct experience with scalable web applications aligns perfectly with backend development roles.', required_skills=['Python', 'cloud technologies', 'API development'], years_required=5), JobRecommendation(job_title='DevOps Engineer', job_level='Mid-level', confidence=0.7, reasoning='Experience with cloud technologies indicates a good fit for DevOps roles.', required_skills=['Python', 'cloud technologies', 'automation'], years_required=3)]

=== Testing triage of job fit ===
is_suitable=False confidence_score=0.7 is_outdated=False reason='Lacks specific experience with FastAPI/Django, which is critical for the role.' missing_skills=['FastAPI', 'Django'] matching_skills=['Python', 'backend development experience']

=== Testing resume-job comparison ===
skill_match=0.75 experience_match=1.0 level_match=1.0 overall_score=0.85 red_flags=[] green_flags=['8+ years of experience in software engineering', 'Expert in Python']
"""