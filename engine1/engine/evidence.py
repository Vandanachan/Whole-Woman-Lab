"""Evidence layer — lift Facts into Evidence and index them for scoring.

The evidence graph itself (evidence -> hypotheses) is materialised during
scoring, where the edges (EvidenceLink) are created as patterns match.
"""
from __future__ import annotations

from .models import Evidence, Fact


def build_evidence(facts: list[Fact]) -> dict[str, Evidence]:
    """Map each fact-code to an Evidence object (deterministic, sorted input)."""
    index: dict[str, Evidence] = {}
    for f in facts:
        index[f.code] = Evidence(
            code=f.code, label=f.label, objective=f.objective, quality=f.quality
        )
    return index
