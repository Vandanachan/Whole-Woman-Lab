"""Differential layer — rank the active hypotheses transparently."""
from __future__ import annotations

from .models import Confidence, DifferentialItem, Hypothesis


def build_differential(
    hyps: dict[str, Hypothesis],
    confidences: dict[str, Confidence],
    present_threshold: float,
    tendency_threshold: float,
    suppressed: set[str],
    max_items: int,
) -> list[DifferentialItem]:
    ranked = sorted(
        (pid for pid in hyps if confidences[pid].value >= tendency_threshold),
        key=lambda p: (-confidences[p].value, -hyps[p].normalized, p),
    )
    items: list[DifferentialItem] = []
    rank = 0
    for pid in ranked:
        if pid in suppressed:
            continue
        rank += 1
        if rank > max_items:
            break
        c = confidences[pid]
        h = hyps[pid]
        status = "present" if c.value >= present_threshold else "tendency"
        items.append(DifferentialItem(
            rank=rank, pattern_id=pid, name=h.name, status=status,
            confidence=c.value, normalized_score=h.normalized,
            key_evidence=tuple(h.supporting[:6]),
        ))
    return items
