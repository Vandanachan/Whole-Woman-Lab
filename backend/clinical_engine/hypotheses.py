"""Hypothesis layer — instantiate one competing Hypothesis per catalogue pattern.

Rule 2: evidence generates hypotheses. Every pattern that *could* be supported
is seeded; scoring then lets them compete (Rule 3). ``max_possible`` is
pre-computed with the same objective multiplier scoring uses, so the normalised
score always lands in [0, 1].
"""
from __future__ import annotations

from .models import Hypothesis


def max_possible_for(pattern: dict, catalogue: dict[str, dict], obj_mult: float) -> float:
    total = 0.0
    for exp in pattern["expected_evidence"]:
        code = exp["code"]
        meta = catalogue.get(code, {})
        mult = obj_mult if meta.get("objective") else 1.0
        total += float(exp["weight"]) * mult
    return round(total, 4)


def generate_hypotheses(
    patterns: list[dict], catalogue: dict[str, dict], obj_mult: float
) -> dict[str, Hypothesis]:
    hyps: dict[str, Hypothesis] = {}
    for p in sorted(patterns, key=lambda x: x["pattern_id"]):
        hyps[p["pattern_id"]] = Hypothesis(
            pattern_id=p["pattern_id"],
            name=p["name"],
            thermal=p["thermal"],
            excess_deficiency=p["excess_deficiency"],
            can_be_root=bool(p["can_be_root"]),
            max_possible=max_possible_for(p, catalogue, obj_mult),
            treatment_principle=p["treatment_principle"],
            formulas=list(p["formulas"]),
            caution=p.get("caution"),
            unmet_expected=[e["code"] for e in p["expected_evidence"]],
        )
    return hyps
