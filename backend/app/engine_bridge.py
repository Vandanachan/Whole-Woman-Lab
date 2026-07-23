"""Bridge between the API and the deterministic Engine 1.

Loads the engine + knowledge base once at import (cheap, read-only) and exposes
a validated run() plus the finding catalogue used to build the questionnaire.
"""
from __future__ import annotations

from pathlib import Path

from clinical_engine import Engine, EngineResult

# backend/data holds the vendored knowledge base
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_engine = Engine(DATA_DIR)


def catalogue() -> dict[str, dict]:
    return _engine.catalogue


def known_codes() -> set[str]:
    return set(_engine.catalogue.keys())


def run(codes: list[str], case_id: str = "case") -> EngineResult:
    """Validate incoming codes then run deterministic reasoning."""
    valid = known_codes()
    unknown = [c for c in codes if c not in valid]
    if unknown:
        raise ValueError(f"Unknown finding codes: {', '.join(sorted(unknown))}")
    return _engine.run(codes, case_id=case_id)
