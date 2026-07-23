"""Diagnosis layer — the explainable final objects (Rules 4 & 5).

A hypothesis becomes a Diagnosis only when its (post-conflict) confidence meets
the diagnosis threshold, it was not suppressed by conflict resolution, and no
contradiction touching it is left unresolved. Every Diagnosis carries evidence,
role (root/branch), confidence, priority and a written explanation.
"""
from __future__ import annotations

from .models import Confidence, Diagnosis, Hypothesis, ProgressionPath, Resolution


def _priority(conf_value: float, excess_deficiency: str) -> tuple[str, float]:
    numeric = round(conf_value * 100.0, 1)
    if excess_deficiency == "deficiency":
        numeric = round(min(100.0, numeric + 5.0), 1)  # depletion is foundational
    if numeric >= 75:
        level = "high"
    elif numeric >= 55:
        level = "moderate"
    elif numeric >= 35:
        level = "routine"
    else:
        level = "monitor"
    return level, numeric


def build_diagnoses(
    hyps: dict[str, Hypothesis],
    confidences: dict[str, Confidence],
    progression: ProgressionPath,
    resolutions: list[Resolution],
    suppressed: set[str],
    diagnosis_threshold: float,
) -> list[Diagnosis]:
    unresolved = {r for r in resolutions if r.status not in {"resolved"}}
    if unresolved:
        # Rule 4: withhold all diagnoses until contradictions are resolved.
        return []

    out: list[Diagnosis] = []
    for pid in sorted(hyps, key=lambda p: -confidences[p].value):
        c = confidences[pid]
        if pid in suppressed or c.value < diagnosis_threshold:
            continue
        h = hyps[pid]
        if pid in progression.roots:
            role = "root"
        elif pid in progression.branches:
            role = "branch"
        else:
            role = "co-primary"
        level, numeric = _priority(c.value, h.excess_deficiency)
        n_obj = sum(1 for _ in [x for x in h.supporting]) if h.supporting else 0
        explanation = (
            f"{h.name} ({role}) — confidence {c.value:.0%} ({c.band}). "
            f"Supported by {len(h.supporting)} findings "
            f"(objective weight {h.supporting_objective_weight:.1f} of {h.supporting_total_weight:.1f}). "
            f"Principle: {h.treatment_principle}"
        )
        out.append(Diagnosis(
            pattern_id=pid, name=h.name, role=role, confidence=c,
            priority_level=level, priority_numeric=numeric,
            evidence=tuple(h.supporting), treatment_principle=h.treatment_principle,
            formulas=tuple(h.formulas), caution=h.caution, explanation=explanation,
        ))
    # roots first, then branches, then co-primary; stable by confidence within
    order = {"root": 0, "co-primary": 1, "branch": 2}
    out.sort(key=lambda d: (order.get(d.role, 3), -d.confidence.value))
    return out
