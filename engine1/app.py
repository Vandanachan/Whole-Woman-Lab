#!/usr/bin/env python3
"""Engine 1 demo runner.

Runs the deterministic clinical-reasoning engine on a sample case and prints a
readable summary of the structured output (the same dict an LLM would render to
prose in the Report engine). Usage:

    python app.py                # runs the built-in sample case
    python app.py CODE1 CODE2 …  # runs on an explicit list of finding codes
"""
from __future__ import annotations

import sys
from pathlib import Path

from engine.reasoning import Engine

DATA = Path(__file__).parent / "data"

# Sample case (the "yin/blood-deficient with qi-stagnation, mixed" presentation)
SAMPLE = [
    "KNOWN_YIN_DEF", "KNOWN_BLOOD_DEF",
    "TONGUE_RED", "TONGUE_CENTRAL_CRACK", "TONGUE_TIP_RED", "TONGUE_SIDES_RED",
    "PULSE_THIN", "PULSE_RAPID", "PULSE_WIRY", "PULSE_WEAK",
    "DRY_EYES_SKIN", "TIRED_WIRED", "WAKE_1_3AM",
    "STOOL_DRY_FRAGMENTED", "STOOL_LOOSE", "STOOL_MUCUS", "STOOL_ALTERNATING",
    "GAS_BLOATING", "IRRITABILITY", "SIGHING", "WORSE_STRESS",
    "COLD_LIMBS", "FATIGUE",
]


def _rule(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def main(codes: list[str]) -> None:
    engine = Engine(DATA)
    result = engine.run(codes, case_id="demo")
    r = result.report

    print("=" * 68)
    print("WHOLE WOMAN LAB — ENGINE 1 · CLINICAL REASONING")
    print("=" * 68)
    print("\nHEADLINE:", r["headline"])

    _rule("CONFIRMED DIAGNOSES (past confidence + contradiction gate)")
    if not r["diagnoses"]:
        print("  (none reached the diagnosis threshold)")
    for d in r["diagnoses"]:
        print(f"  • {d['pattern']}  [{d['role']}]  {d['confidence']:.0%} ({d['band']}) "
              f"· priority {d['priority']}")
        print(f"      principle: {d['principle']}")
        print(f"      formulas : {', '.join(d['formulas'])}")

    _rule("DIFFERENTIAL (all active hypotheses, ranked)")
    for i in r["differential"]:
        print(f"  {i['rank']}. {i['pattern']:<22} {i['status']:<9} conf {i['confidence']:.0%}")

    _rule("ROOT vs BRANCH & PROGRESSION")
    p = r["progression"]
    print(f"  roots   : {', '.join(p['roots']) or '—'}")
    print(f"  branches: {', '.join(p['branches']) or '—'}")
    print(f"  heading : {', '.join(p['projected_next']) or '—'}  ({p['reversibility']})")
    for m in p["mechanisms"]:
        print(f"      {m['from']} --{m['relation']}--> {m['to']}: {m['mechanism']}")

    if r["safety"]:
        _rule("⚠ SAFETY GUARDRAILS")
        for s in r["safety"]:
            print(f"  [{s['severity'].upper()}] {s['message']}")

    _rule("REASONING TRACE")
    for step in result.trace:
        print(f"  · {step.stage}: {step.description}")

    print("\n" + "-" * 68)
    print(r["disclaimer"])


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args if args else SAMPLE)
