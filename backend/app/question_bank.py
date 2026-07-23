"""Build the intake questionnaire schema directly from the engine's finding
catalogue, so questions and scoring can never drift out of sync.

Every finding-code becomes a selectable option; the frontend renders checklists
and submits the codes the practitioner/client selected.
"""
from __future__ import annotations

SECTIONS = [
    ("symptom", "Symptoms", "Tick every symptom the client currently experiences."),
    ("tongue", "Tongue findings", "Objective — what you observe on the tongue."),
    ("pulse", "Pulse findings", "Objective — overall pulse qualities."),
    ("history", "Known / confirmed", "Anything already established (labs, prior dx)."),
]


def build_schema(catalogue: dict[str, dict]) -> list[dict]:
    by_modality: dict[str, list[dict]] = {}
    for code, meta in catalogue.items():
        by_modality.setdefault(meta["modality"], []).append(
            {"code": code, "label": meta["label"]}
        )
    for opts in by_modality.values():
        opts.sort(key=lambda o: o["label"])

    schema: list[dict] = []
    for key, title, hint in SECTIONS:
        opts = by_modality.get(key, [])
        if not opts:
            continue
        schema.append(
            {"key": key, "title": title, "hint": hint, "input": "checklist", "options": opts}
        )
    return schema
