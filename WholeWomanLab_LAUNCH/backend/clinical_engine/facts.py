"""Facts layer — normalise raw input codes into immutable ClinicalFacts.

Rule 1: everything is evidence. The input to the engine is simply the set of
present findings (their canonical codes); this module attaches the catalogue
metadata (label, modality, objectivity, data-quality) and rejects unknowns.
"""
from __future__ import annotations

from .models import Fact


def build_facts(
    present_codes: list[str],
    catalogue: dict[str, dict],
    data_confidence: dict[str, float],
) -> list[Fact]:
    """Deterministically turn present finding-codes into normalised Facts."""
    facts: list[Fact] = []
    seen: set[str] = set()
    for code in sorted(set(present_codes)):
        if code in seen:
            continue
        seen.add(code)
        meta = catalogue.get(code)
        if meta is None:
            raise KeyError(f"Unknown evidence code: {code!r} (not in evidence.json)")
        etype = meta["type"]
        facts.append(
            Fact(
                code=code,
                label=meta["label"],
                modality=meta["modality"],
                etype=etype,
                objective=bool(meta["objective"]),
                quality=float(data_confidence.get(etype, 1.0)),
            )
        )
    return facts
