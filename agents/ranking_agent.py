"""Ranking agent - Rank and select top job matches."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.schemas import (
    ComparisonResult,
    JobItem,
    RankedJobResult,
)


class RankingAgent:
    """Rank job candidates and select top matches."""

    # Weights for final rank score (must sum to 1.0)
    WEIGHTS = {
        "match_score": 0.50,
        "confidence": 0.25,
        "freshness": 0.15,
        "flags": 0.10,
    }
    
    MAX_FRESH_DAYS = 60
    TOP_N_RESULTS = 10

    async def run(
        self,
        comparison_results: list[ComparisonResult],
        job_items: list[JobItem],
    ) -> tuple[list[RankedJobResult], dict[str, Any]]:
        """Rank job candidates."""
        # Build ranking for each comparison
        ranked = []
        
        for idx, (comparison, job_item) in enumerate(zip(comparison_results, job_items)):
            rank_score = self._compute_rank_score(comparison, job_item)
            reasons = self._build_rank_reasons(comparison, job_item, rank_score)
            
            result = RankedJobResult(
                rank=idx + 1,
                job_url=str(comparison.candidate_job.job_url),
                job_title=comparison.candidate_job.job_title,
                company=comparison.candidate_job.company,
                match_score=comparison.match_score,
                confidence=job_item.confidence,
                key_reasons=reasons,
            )
            ranked.append((result, rank_score))
        
        # Sort by rank score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        # Update ranks after sorting
        final_results = []
        for idx, (result, _) in enumerate(ranked[:self.TOP_N_RESULTS]):
            result.rank = idx + 1
            final_results.append(result)
        
        return final_results, {
            "total_comparisons": len(comparison_results),
            "top_results_returned": len(final_results),
            "ranking_complete": True,
        }

    def _compute_rank_score(self, comparison: ComparisonResult, job_item: JobItem) -> float:
        """Compute final rank score."""
        # Individual component scores
        match_score = comparison.match_score
        confidence_score = job_item.confidence
        freshness_score = self._compute_freshness(comparison.candidate_job.posted_date)
        flags_score = self._compute_flags_score(comparison.green_flags, comparison.red_flags)
        
        # Weighted sum
        total = (
            match_score * self.WEIGHTS["match_score"]
            + confidence_score * self.WEIGHTS["confidence"]
            + freshness_score * self.WEIGHTS["freshness"]
            + flags_score * self.WEIGHTS["flags"]
        )
        
        return min(1.0, max(0.0, total))

    @staticmethod
    def _compute_freshness(posted_date: datetime) -> float:
        """Score posting freshness."""
        days_old = (datetime.now(timezone.utc) - posted_date).days
        
        if days_old <= 7:
            return 1.0
        elif days_old <= 30:
            return 0.85
        elif days_old <= 60:
            return 0.65
        elif days_old <= 90:
            return 0.45
        else:
            return 0.2

    @staticmethod
    def _compute_flags_score(green_flags: list[str], red_flags: list[str]) -> float:
        """Score based on flag balance."""
        flag_balance = len(green_flags) - len(red_flags)
        
        if flag_balance >= 2:
            return 1.0
        elif flag_balance >= 1:
            return 0.8
        elif flag_balance >= 0:
            return 0.6
        elif flag_balance >= -1:
            return 0.4
        else:
            return 0.2

    @staticmethod
    def _build_rank_reasons(
        comparison: ComparisonResult,
        job_item: JobItem,
        rank_score: float,
    ) -> list[str]:
        """Build human-readable ranking reasons."""
        reasons = []
        
        # Match quality
        if comparison.match_score > 0.8:
            reasons.append("Excellent skill match")
        elif comparison.match_score > 0.6:
            reasons.append("Good experience fit")
        
        # Green flags
        if comparison.green_flags:
            reasons.extend(comparison.green_flags[:2])
        
        # Freshness
        days_old = (datetime.now(timezone.utc) - comparison.candidate_job.posted_date).days
        if days_old <= 7:
            reasons.append("Recently posted")
        
        # Overall assessment
        if rank_score > 0.8:
            reasons.append("Top tier match")
        elif rank_score > 0.6:
            reasons.append("Strong candidate")
        
        return reasons[:5]  # Limit to 5 reasons

    (0.80, "Highly recommended"),
    (0.65, "Strong match — apply soon"),
    (0.50, "Consider applying"),
    (0.35, "Worth a look"),
    (0.00, "Long shot — apply if interested"),

TOP_N = 10


def _freshness_score(item: JobItem) -> float:
    """0–1 freshness from posting_age_days stored in supporting_data."""
    age = item.supporting_data.get("posting_age_days", MAX_FRESH_DAYS)
    return max(0.0, 1.0 - age / MAX_FRESH_DAYS)


def _flag_score(item: JobItem) -> float:
    """Normalised net flag balance: +1 = all green, -1 = all red."""
    greens = len(item.supporting_data.get("green_flags", []))
    reds   = len(item.red_flags)
    total  = greens + reds
    if total == 0:
        return 0.5  # neutral
    return (greens - reds) / total * 0.5 + 0.5  # map [-1,1] → [0,1]


def _rank_score(item: JobItem) -> float:
    return round(
        item.match_score  * _W_MATCH
        + item.confidence * _W_CONFIDENCE
        + _freshness_score(item) * _W_FRESHNESS
        + _flag_score(item)      * _W_FLAGS,
        4,
    )


def _recommendation(score: float) -> str:
    for threshold, label in _TIERS:
        if score >= threshold:
            return label
    return _TIERS[-1][1]


def _build_reason(item: JobItem, rank_score: float) -> str:
    """
    One-sentence reason that references the strongest evidence signal.
    Mirrors TinyDetective's _build_reason pattern.
    """
    breakdown = item.supporting_data.get("score_breakdown", {})
    skill_pct  = round(item.supporting_data.get("skill_coverage", 0) * 100)
    exp_delta  = item.supporting_data.get("experience_delta", 0)
    age        = item.supporting_data.get("posting_age_days", "?")
    greens     = item.supporting_data.get("green_flags", [])
    reds       = item.red_flags

    parts: list[str] = []

    # Lead with strongest positive signal
    if skill_pct >= 80:
        parts.append(f"{skill_pct}% skill coverage")
    elif skill_pct >= 50:
        parts.append(f"moderate skill overlap ({skill_pct}%)")
    else:
        parts.append(f"partial skill match ({skill_pct}%)")

    # Experience context
    if exp_delta >= 0:
        parts.append(f"{exp_delta}yr experience surplus" if exp_delta else "experience requirement met")
    else:
        parts.append(f"{abs(exp_delta)}yr below requirement")

    # Freshness
    if isinstance(age, int) and age <= 7:
        parts.append("posted this week")
    elif isinstance(age, int) and age <= 30:
        parts.append(f"posted {age}d ago")
    else:
        parts.append(f"listing is {age}d old")

    # Flag summary
    if reds:
        parts.append("flags: " + ", ".join(reds[:2]))
    elif greens:
        parts.append("no red flags")

    return "; ".join(parts) + "."


class RankingAgent:
    """Rank JobItems and return the top N with reasons."""

    def __init__(self, top_n: int = TOP_N) -> None:
        self.top_n = top_n

    def run(
        self,
        comparisons: list[ComparisonResult],  # kept for future cross-referencing
        job_items: list[JobItem],
    ) -> list[RankedJobResult]:
        """
        Score, sort, and annotate job_items.
        Returns at most self.top_n RankedJobResult objects.
        """
        if not job_items:
            return []

        scored = sorted(
            job_items,
            key=_rank_score,
            reverse=True,
        )[: self.top_n]

        results: list[RankedJobResult] = []
        for rank, item in enumerate(scored, start=1):
            score = _rank_score(item)
            results.append(
                RankedJobResult(
                    rank=rank,
                    job_item=item,
                    match_reason=_build_reason(item, score),
                    recommendation=_recommendation(score),
                )
            )
        return results