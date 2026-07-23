"""Confidence layer — transparent, bounded confidence per hypothesis.

Confidence blends three fully-visible components:
  * score      : normalised evidence match (raw / max_possible)
  * objective  : fraction of the support that is objective (tongue/pulse/labs)
  * coverage   : breadth of corroboration (distinct supporting findings)
Every component and weight is reported, so a confidence figure is never a
black box. Contradiction penalties are applied later by the conflict layer.
"""
from __future__ import annotations

from .models import Confidence, ConfidenceComponent, Hypothesis


def _band(v: float) -> str:
    if v < 0.20:
        return "very_low"
    if v < 0.40:
        return "low"
    if v < 0.60:
        return "moderate"
    if v < 0.80:
        return "high"
    return "very_high"


def compute_confidence(
    h: Hypothesis, cfg_weights: dict[str, float], coverage_target: int, threshold: float
) -> Confidence:
    score = h.normalized
    objective = (
        round(h.supporting_objective_weight / h.supporting_total_weight, 4)
        if h.supporting_total_weight > 0
        else 0.0
    )
    coverage = round(min(1.0, len(h.supporting) / max(1, coverage_target)), 4)
    comps = (
        ConfidenceComponent("score", score, cfg_weights["score"]),
        ConfidenceComponent("objective_corroboration", objective, cfg_weights["objective"]),
        ConfidenceComponent("coverage", coverage, cfg_weights["coverage"]),
    )
    value = round(sum(c.contribution for c in comps), 4)
    value = max(0.0, min(1.0, value))
    return Confidence(value=value, band=_band(value), components=comps, threshold=threshold)
