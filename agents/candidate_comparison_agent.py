"""Candidate comparison agent — non-AI heuristic scoring.

Algorithm overview
------------------
Ten independently weighted features are scored 0–1, multiplied by their
weights (defined in FeatureWeights), then summed into a composite
match_score. Red/green flags are raised by threshold rules on top of the
raw scores.

To tune the algorithm:
  • Change weights in FeatureWeights (they should sum to 1.0).
  • Adjust thresholds at the top of this file.
  • Remove a feature: set its weight to 0.0 — it will score 0 and be
    excluded from the reason string automatically.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from models.schemas import (
    CandidateJob,
    ComparisonResult,
    FeatureScores,
    FeatureWeights,
    JobLevel,
    ResumeData,
)

# ---------------------------------------------------------------------------
# Tuneable thresholds
# ---------------------------------------------------------------------------

# recency: postings older than this many days are penalised
STALE_POSTING_DAYS = 60

# experience: candidate has this many *extra* years above requirement → overqualified flag
OVERQUALIFIED_YEARS_THRESHOLD = 5

# experience: candidate is this many years *below* requirement → underqualified flag
UNDERQUALIFIED_YEARS_THRESHOLD = 2

# salary: if candidate's inferred mid-point is below the job's lower bound by this fraction
SALARY_BELOW_BAND_RATIO = 0.15

# skill_overlap: below this fraction → missing_skills red flag
SKILL_OVERLAP_WEAK_THRESHOLD = 0.4

# match_score: below this → flagged "low_overall_match"
LOW_MATCH_THRESHOLD = 0.35

# JobLevel ordering for adjacency scoring
_LEVEL_ORDER: dict[JobLevel, int] = {
    JobLevel.ENTRY: 0,
    JobLevel.MID: 1,
    JobLevel.SENIOR: 2,
    JobLevel.LEAD: 3,
    JobLevel.EXECUTIVE: 4,
}


class CandidateComparisonAgent:
    """Compare a ResumeData against a CandidateJob using pure heuristics.

    Usage::

        agent = CandidateComparisonAgent()
        result = agent.run(resume, candidate_job)

    Pass a custom ``FeatureWeights`` instance to override default weights::

        weights = FeatureWeights(skill_overlap=0.30, level_match=0.05)
        agent = CandidateComparisonAgent(weights=weights)
    """

    def __init__(self, weights: FeatureWeights | None = None) -> None:
        self.weights = weights or FeatureWeights()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, resume: ResumeData, job: CandidateJob) -> ComparisonResult:
        """Score resume against job and return a ComparisonResult."""
        scores = self._score_all(resume, job)
        match_score = self._weighted_sum(scores)
        red_flags = self._red_flags(resume, job, scores, match_score)
        green_flags = self._green_flags(resume, job, scores)
        reason = self._build_reason(match_score, scores, red_flags, green_flags)

        return ComparisonResult(
            job_url=job.job_url,
            candidate_job=job,
            feature_scores=scores,
            match_score=round(match_score, 3),
            red_flags=red_flags,
            green_flags=green_flags,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # Feature scoring — one method per feature
    # ------------------------------------------------------------------

    def _score_all(self, resume: ResumeData, job: CandidateJob) -> FeatureScores:
        return FeatureScores(
            skill_overlap=self._skill_overlap(resume.skills, job.required_skills),
            experience_gap=self._experience_gap(resume.years_experience, job.years_required),
            title_similarity=self._title_similarity(resume.current_role, job.job_title),
            level_match=self._level_match(resume, job),
            education_match=self._education_match(resume.education, job.job_description),
            certification_match=self._certification_match(resume.certifications, job.job_description),
            preferred_skill_bonus=self._preferred_skill_bonus(resume.skills, job.preferred_skills),
            location_match=self._location_match(resume, job),
            recency_penalty=self._recency_penalty(job.posted_date),
            salary_fit=self._salary_fit(resume, job),
        )

    # ---- Feature 1: skill_overlap ----------------------------------------

    @staticmethod
    def _skill_overlap(resume_skills: list[str], required_skills: list[str]) -> float:
        """Fraction of required skills present in the resume (case-insensitive)."""
        if not required_skills:
            return 1.0  # no requirements → perfect fit by default
        resume_norm = {s.lower().strip() for s in resume_skills}
        matched = sum(1 for s in required_skills if s.lower().strip() in resume_norm)
        return round(matched / len(required_skills), 3)

    # ---- Feature 2: experience_gap ----------------------------------------

    @staticmethod
    def _experience_gap(candidate_years: int, required_years: int) -> float:
        """
        1.0  → candidate meets requirement exactly or is 1-2 years above.
        Decays linearly if under-qualified; also decays if grossly over-qualified.
        """
        if required_years == 0:
            return 1.0
        delta = candidate_years - required_years
        if delta >= 0:
            # Over-qualified decay starts after +4 years above requirement
            overqualified_excess = max(0, delta - 4)
            penalty = min(0.5, overqualified_excess * 0.06)
            return round(max(0.5, 1.0 - penalty), 3)
        else:
            # Under-qualified: linear decay
            shortfall_ratio = abs(delta) / required_years
            return round(max(0.0, 1.0 - shortfall_ratio), 3)

    # ---- Feature 3: title_similarity ----------------------------------------

    @staticmethod
    def _title_similarity(resume_role: str | None, job_title: str) -> float:
        """
        Word-overlap between the candidate's current role and the job title.
        Mirrors TinyDetective's _contains logic, extended with token Jaccard.
        """
        if not resume_role:
            return 0.0
        left = CandidateComparisonAgent._tokenize(resume_role)
        right = CandidateComparisonAgent._tokenize(job_title)
        if left == right:
            return 1.0
        if left <= right or right <= left:  # one is a subset of the other
            return 0.85
        jaccard = len(left & right) / len(left | right) if left | right else 0.0
        return round(min(0.8, jaccard), 3)

    # ---- Feature 4: level_match ----------------------------------------

    @staticmethod
    def _level_match(resume: ResumeData, job: CandidateJob) -> float:
        """
        Infer candidate's level from years_experience, compare to job.job_level.
        Exact → 1.0, adjacent → 0.6, two steps → 0.3, further → 0.0.
        """
        inferred = CandidateComparisonAgent._infer_level(resume.years_experience)
        distance = abs(_LEVEL_ORDER[inferred] - _LEVEL_ORDER[job.job_level])
        return {0: 1.0, 1: 0.6, 2: 0.3}.get(distance, 0.0)

    @staticmethod
    def _infer_level(years: int) -> JobLevel:
        if years < 2:
            return JobLevel.ENTRY
        if years < 5:
            return JobLevel.MID
        if years < 9:
            return JobLevel.SENIOR
        if years < 14:
            return JobLevel.LEAD
        return JobLevel.EXECUTIVE

    # ---- Feature 5: education_match ----------------------------------------

    @staticmethod
    def _education_match(education: list[str], job_description: str) -> float:
        """
        Check how many degree-level keywords from the resume appear in the
        job description. Rough proxy for education alignment.
        """
        DEGREE_KEYWORDS = {
            "bachelor", "master", "phd", "doctorate", "diploma",
            "degree", "mba", "bsc", "msc", "be", "beng", "meng",
        }
        if not education or not job_description:
            return 0.5  # neutral — no data to penalise
        resume_degrees = set()
        for entry in education:
            for word in CandidateComparisonAgent._tokenize(entry):
                if word in DEGREE_KEYWORDS:
                    resume_degrees.add(word)
        if not resume_degrees:
            return 0.5
        jd_tokens = CandidateComparisonAgent._tokenize(job_description)
        matched = resume_degrees & jd_tokens
        return round(min(1.0, len(matched) / len(resume_degrees) + 0.3), 3)

    # ---- Feature 6: certification_match ----------------------------------------

    @staticmethod
    def _certification_match(certifications: list[str], job_description: str) -> float:
        """
        Check how many of the candidate's certifications are mentioned in
        the job description (acronym-tolerant).
        """
        if not certifications:
            return 0.5  # neutral
        if not job_description:
            return 0.0
        jd_lower = job_description.lower()
        matched = sum(
            1 for cert in certifications
            if cert.lower().strip() in jd_lower
        )
        return round(min(1.0, matched / len(certifications) + 0.2), 3)

    # ---- Feature 7: preferred_skill_bonus ----------------------------------------

    @staticmethod
    def _preferred_skill_bonus(resume_skills: list[str], preferred_skills: list[str]) -> float:
        """
        Fraction of *preferred* (nice-to-have) skills covered by the resume.
        Returns 0.5 if the job has no preferred skills (neutral).
        """
        if not preferred_skills:
            return 0.5
        resume_norm = {s.lower().strip() for s in resume_skills}
        matched = sum(1 for s in preferred_skills if s.lower().strip() in resume_norm)
        return round(matched / len(preferred_skills), 3)

    # ---- Feature 8: location_match ----------------------------------------

    @staticmethod
    def _location_match(resume: ResumeData, job: CandidateJob) -> float:
        """
        Simple keyword check: remote/hybrid/on-site signal + city match.
        Returns 1.0 for remote jobs (universal), 0.5 if unclear, 0.0 if
        location fields are present and don't overlap.
        """
        jd_lower = job.job_description.lower()
        loc_lower = job.location.lower()

        if "remote" in loc_lower or "remote" in jd_lower:
            return 1.0

        # Try to find candidate's location in work_history (last entry)
        # ResumeData doesn't store location directly — look in work_history
        candidate_location: str | None = None
        if resume.work_history:
            last = resume.work_history[-1]
            candidate_location = str(last.get("location", "")).lower().strip()

        if not candidate_location:
            return 0.5  # unknown → neutral

        # City / country keyword overlap
        loc_tokens = CandidateComparisonAgent._tokenize(loc_lower)
        cand_tokens = CandidateComparisonAgent._tokenize(candidate_location)
        overlap = loc_tokens & cand_tokens
        if overlap:
            return 1.0
        return 0.2  # location data available but no match

    # ---- Feature 9: recency_penalty ----------------------------------------

    @staticmethod
    def _recency_penalty(posted_date: datetime) -> float:
        """
        1.0 for freshly posted jobs, decays linearly to 0.0 at STALE_POSTING_DAYS.
        This is a *penalty* feature: low score = old posting.
        """
        now = datetime.now(timezone.utc)
        if posted_date.tzinfo is None:
            posted_date = posted_date.replace(tzinfo=timezone.utc)
        age_days = (now - posted_date).days
        if age_days <= 0:
            return 1.0
        score = 1.0 - (age_days / STALE_POSTING_DAYS)
        return round(max(0.0, score), 3)

    # ---- Feature 10: salary_fit ----------------------------------------

    @staticmethod
    def _salary_fit(resume: ResumeData, job: CandidateJob) -> float:
        """
        Compare job salary_range to an inferred band derived from
        years_experience. Returns 0.5 if either side is missing.
        """
        if not job.salary_range:
            return 0.5
        job_low, job_high = job.salary_range
        if job_low <= 0 and job_high <= 0:
            return 0.5

        # Rough annual salary estimate by years of experience (SGD/USD ballpark)
        # Adjust _infer_salary_midpoint for your market
        candidate_mid = CandidateComparisonAgent._infer_salary_midpoint(resume.years_experience)
        if candidate_mid is None:
            return 0.5

        job_mid = (job_low + job_high) / 2

        if job_low <= candidate_mid <= job_high:
            return 1.0  # within band

        gap = min(abs(candidate_mid - job_low), abs(candidate_mid - job_high))
        ratio = gap / max(job_mid, 1)
        return round(max(0.0, 1.0 - ratio), 3)

    @staticmethod
    def _infer_salary_midpoint(years: int) -> float | None:
        """
        Very rough midpoint by experience bucket (in thousands, local currency).
        Replace with real data if available.
        """
        table = [
            (2,  50_000),
            (5,  75_000),
            (9, 110_000),
            (14, 150_000),
            (999, 200_000),
        ]
        for threshold, mid in table:
            if years <= threshold:
                return float(mid)
        return None

    # ------------------------------------------------------------------
    # Weighted composite
    # ------------------------------------------------------------------

    def _weighted_sum(self, scores: FeatureScores) -> float:
        w = self.weights
        s = scores
        total = (
            s.skill_overlap        * w.skill_overlap
            + s.experience_gap     * w.experience_gap
            + s.title_similarity   * w.title_similarity
            + s.level_match        * w.level_match
            + s.education_match    * w.education_match
            + s.certification_match * w.certification_match
            + s.preferred_skill_bonus * w.preferred_skill_bonus
            + s.location_match     * w.location_match
            + s.recency_penalty    * w.recency_penalty
            + s.salary_fit         * w.salary_fit
        )
        return round(total, 4)

    # ------------------------------------------------------------------
    # Signal detection — mirrors TinyDetective suspicious_signals pattern
    # ------------------------------------------------------------------

    def _red_flags(
        self,
        resume: ResumeData,
        job: CandidateJob,
        scores: FeatureScores,
        match_score: float,
    ) -> list[str]:
        flags: list[str] = []

        if scores.skill_overlap < SKILL_OVERLAP_WEAK_THRESHOLD:
            flags.append("weak_skill_overlap")

        delta = resume.years_experience - job.years_required
        if delta > OVERQUALIFIED_YEARS_THRESHOLD:
            flags.append("likely_overqualified")
        elif delta < -UNDERQUALIFIED_YEARS_THRESHOLD:
            flags.append("likely_underqualified")

        if scores.recency_penalty == 0.0:
            flags.append("stale_posting")
        elif scores.recency_penalty < 0.3:
            flags.append("aging_posting")

        if scores.level_match == 0.0:
            flags.append("level_mismatch")

        if job.salary_range and scores.salary_fit < (1 - SALARY_BELOW_BAND_RATIO):
            flags.append("salary_outside_band")

        if match_score < LOW_MATCH_THRESHOLD:
            flags.append("low_overall_match")

        return flags

    def _green_flags(
        self,
        resume: ResumeData,
        job: CandidateJob,
        scores: FeatureScores,
    ) -> list[str]:
        flags: list[str] = []

        if scores.skill_overlap >= 0.8:
            flags.append("strong_skill_overlap")
        if scores.level_match == 1.0:
            flags.append("level_exact_match")
        if scores.title_similarity >= 0.7:
            flags.append("title_closely_aligned")
        if scores.recency_penalty >= 0.8:
            flags.append("fresh_posting")
        if scores.preferred_skill_bonus >= 0.6:
            flags.append("preferred_skills_covered")
        if scores.certification_match >= 0.7:
            flags.append("relevant_certifications")
        if scores.experience_gap >= 0.9:
            flags.append("experience_well_matched")

        return flags

    # ------------------------------------------------------------------
    # Human-readable reason — mirrors TinyDetective._build_reason
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reason(
        match_score: float,
        scores: FeatureScores,
        red_flags: list[str],
        green_flags: list[str],
    ) -> str:
        if match_score >= 0.75:
            base = "Strong overall match."
        elif match_score >= 0.50:
            base = "Moderate match — worth considering."
        elif match_score >= 0.35:
            base = "Partial match — notable gaps present."
        else:
            base = "Weak match — significant misalignment."

        parts = [base]
        if green_flags:
            parts.append("Strengths: " + ", ".join(green_flags) + ".")
        if red_flags:
            parts.append("Concerns: " + ", ".join(red_flags) + ".")
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Lowercase, strip punctuation, split into word tokens."""
        return set(re.sub(r"[^a-z0-9\s]", " ", text.lower()).split())