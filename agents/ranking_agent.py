"""Ranking agent.

Input:  list[ComparisonResult] + list[JobItem]
Output: list[RankedJobResult]  (top 10, sorted best-first)

Pure algorithmic — no AI. Computes a final composite rank_score that
combines match_score, confidence, flag balance, and posting freshness,
then annotates each result with a human-readable reason and a
recommendation tier label.
"""

from __future__ import annotations

from models.schemas import (
    ComparisonResult,
    JobItem,
    RankedJobResult,
)

# Weights for the final rank score (must sum to 1.0)
_W_MATCH      = 0.50   # raw match_score from ComparisonAgent
_W_CONFIDENCE = 0.25   # evidence confidence from EvidenceAgent
_W_FRESHNESS  = 0.15   # recency of posting (via supporting_data)
_W_FLAGS      = 0.10   # net flag balance (green − red)

# Max posting age considered "fresh" (days)
MAX_FRESH_DAYS = 60

# Recommendation tiers by rank_score
_TIERS = [
    (0.80, "Highly recommended"),
    (0.65, "Strong match — apply soon"),
    (0.50, "Consider applying"),
    (0.35, "Worth a look"),
    (0.00, "Long shot — apply if interested"),
]

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