"""Scoring layer — deterministic weighted evidence accumulation.

For every hypothesis, each expected finding that is actually present contributes
    weight  x  data_quality  x  (objective_multiplier if objective else 1)
to the raw score. Objective findings (tongue/pulse/labs/confirmed history) thus
outweigh self-reported symptoms — the objective-over-subjective principle baked
into the maths, not left to interpretation. Produces the evidence-graph edges.
"""
from __future__ import annotations

from .models import Evidence, EvidenceLink, Hypothesis


def score_hypotheses(
    hyps: dict[str, Hypothesis],
    evidence: dict[str, Evidence],
    patterns: list[dict],
    obj_mult: float,
) -> list[EvidenceLink]:
    """Accumulate scores in-place; return the evidence->hypothesis links."""
    links: list[EvidenceLink] = []
    by_id = {p["pattern_id"]: p for p in patterns}

    for pid in sorted(hyps):
        h = hyps[pid]
        pattern = by_id[pid]
        matched: list[str] = []
        unmet: list[str] = []
        for exp in pattern["expected_evidence"]:
            code, w = exp["code"], float(exp["weight"])
            ev = evidence.get(code)
            if ev is None:
                unmet.append(code)
                continue
            mult = obj_mult if ev.objective else 1.0
            contribution = w * ev.quality * mult
            h.raw_score = round(h.raw_score + contribution, 4)
            h.supporting_total_weight = round(h.supporting_total_weight + contribution, 4)
            if ev.objective:
                h.supporting_objective_weight = round(
                    h.supporting_objective_weight + contribution, 4
                )
            matched.append(code)
            links.append(
                EvidenceLink(
                    evidence_code=code, pattern_id=pid, weight=round(contribution, 4),
                    objective=ev.objective,
                )
            )
        h.supporting = sorted(matched)
        h.unmet_expected = sorted(unmet)
    return links
