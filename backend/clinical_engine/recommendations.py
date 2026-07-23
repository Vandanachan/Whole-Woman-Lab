"""Recommendation layer (Engine 4) — turns confirmed diagnoses into an
elaborate, practitioner-ready treatment plan: nutrition (favour/avoid with
taste & thermal reasoning), herb detail, lifestyle guidance, and cross-pattern
reconciliation when more than one pattern is confirmed.

This module performs no clinical reasoning of its own — it looks up and
assembles content from the vendored nutrition/food-therapy knowledge base
(``data/nutrition.json``) for whatever patterns Engine 1 has already
confirmed. It is deterministic: identical diagnoses always yield identical
output.
"""
from __future__ import annotations

from .models import Diagnosis


def _pattern_block(pid: str, nutrition_kb: dict) -> dict | None:
    return nutrition_kb.get("patterns", {}).get(pid)


def _narrative_for(diag: Diagnosis, block: dict) -> str:
    """A short, readable paragraph introducing this pattern's treatment plan."""
    role_phrase = {
        "root": "the root cause behind this picture",
        "branch": "a downstream branch pattern arising from the root",
        "co-primary": "a co-primary pattern carrying equal weight in this picture",
    }.get(diag.role, "part of this picture")
    return (
        f"{diag.name} is {role_phrase}, confirmed at {diag.confidence.value:.0%} confidence. "
        f"{block.get('overview', '')}"
    )


def _collect_master_avoid(blocks: list[tuple[Diagnosis, dict]]) -> list[dict]:
    """Union of every 'avoid' item across confirmed patterns, deduplicated by
    food name, each tagged with which pattern(s) it applies to."""
    merged: dict[str, dict] = {}
    for diag, block in blocks:
        for item in block.get("avoid", []):
            if not isinstance(item, dict):
                continue
            key = item["food"].strip().lower()
            if key not in merged:
                merged[key] = {"food": item["food"], "why": [], "patterns": []}
            reason = f"{item['why']}"
            if reason not in merged[key]["why"]:
                merged[key]["why"].append(reason)
            if diag.name not in merged[key]["patterns"]:
                merged[key]["patterns"].append(diag.name)
    return list(merged.values())


def _collect_favor_highlights(blocks: list[tuple[Diagnosis, dict]], limit_per_pattern: int = 6) -> list[dict]:
    """A condensed 'top favour items' list per pattern, for a quick-reference
    summary at the top of the nutrition section (the full categorised lists
    remain available per-pattern for the detailed pages)."""
    out: list[dict] = []
    for diag, block in blocks:
        favor = block.get("favor", {})
        items: list[str] = []
        for _category, foods in favor.items():
            if not isinstance(foods, list):
                continue
            for f in foods:
                if isinstance(f, dict) and "food" in f:
                    items.append(f["food"])
                if len(items) >= limit_per_pattern:
                    break
            if len(items) >= limit_per_pattern:
                break
        out.append({"pattern": diag.name, "role": diag.role, "top_foods": items})
    return out


def _reconciliation_notes(present_ids: set[str], nutrition_kb: dict) -> list[str]:
    notes: list[str] = []
    for rule in nutrition_kb.get("pattern_interactions", []):
        all_needed = set(rule.get("when_all", []))
        any_needed = set(rule.get("when_any_deficiency", []))
        if all_needed <= present_ids and (not any_needed or any_needed & present_ids):
            notes.append(rule["note"])
    return notes


def _sequencing(diagnoses: list[Diagnosis], nutrition_kb: dict) -> str | None:
    if len(diagnoses) < 2:
        return None
    return nutrition_kb.get("general_sequencing_note")


def build_treatment_plan(diagnoses: list[Diagnosis], nutrition_kb: dict) -> dict:
    """Assemble the full Engine-4 treatment plan for every confirmed diagnosis.

    Returns a dict with:
      - narrative: an elaborate multi-paragraph readable explanation
      - glossary: taste + thermal property glossary (shown once, educational)
      - by_pattern: full detail (favor/avoid/herbs/lifestyle/sample day) per diagnosis
      - master_avoid: deduplicated union of every avoid-item across patterns
      - favor_highlights: condensed top-foods-per-pattern summary
      - reconciliation_notes: cross-pattern conflict/synergy guidance
      - sequencing: root-first prioritisation note (only when 2+ patterns present)
    """
    blocks: list[tuple[Diagnosis, dict]] = []
    for d in diagnoses:
        block = _pattern_block(d.pattern_id, nutrition_kb)
        if block:
            blocks.append((d, block))

    if not blocks:
        return {
            "narrative": (
                "No pattern reached the diagnosis threshold, so a personalised nutrition and "
                "herb plan cannot yet be generated. Gather more objective signs (tongue & pulse) "
                "and re-run the reading."
            ),
            "glossary": {
                "tastes": nutrition_kb.get("taste_glossary", {}),
                "thermal_properties": nutrition_kb.get("thermal_glossary", {}),
            },
            "by_pattern": [],
            "master_avoid": [],
            "favor_highlights": [],
            "reconciliation_notes": [],
            "sequencing": None,
        }

    present_ids = {d.pattern_id for d, _ in blocks}

    narrative_paras = [_narrative_for(d, b) for d, b in blocks]
    intro = (
        "The plan below translates each confirmed pattern into concrete, everyday choices — "
        "what to eat more of, what to avoid and why, which herbs are traditionally used, and how "
        "to live around the pattern day to day. Every recommendation is tied back to the taste and "
        "thermal-property glossary further below, so the reasoning is transparent rather than a "
        "list of rules to follow blindly."
    )
    narrative = intro + "\n\n" + "\n\n".join(narrative_paras)

    by_pattern = []
    for d, block in blocks:
        by_pattern.append({
            "pattern_id": d.pattern_id,
            "pattern": d.name,
            "role": d.role,
            "confidence": d.confidence.value,
            "overview": block.get("overview", ""),
            "favor": block.get("favor", {}),
            "avoid": block.get("avoid", []),
            "cooking_methods": block.get("cooking_methods", {}),
            "meal_rhythm": block.get("meal_rhythm", ""),
            "herbs_detail": block.get("herbs_detail", []),
            "lifestyle": block.get("lifestyle", []),
            "sample_day": block.get("sample_day", {}),
            "caution": block.get("caution"),
        })

    return {
        "narrative": narrative,
        "glossary": {
            "tastes": nutrition_kb.get("taste_glossary", {}),
            "thermal_properties": nutrition_kb.get("thermal_glossary", {}),
            "how_to_read": nutrition_kb.get("how_to_read_this_section", ""),
        },
        "by_pattern": by_pattern,
        "master_avoid": _collect_master_avoid(blocks),
        "favor_highlights": _collect_favor_highlights(blocks),
        "reconciliation_notes": _reconciliation_notes(present_ids, nutrition_kb),
        "sequencing": _sequencing(diagnoses, nutrition_kb),
    }
