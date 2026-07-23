"""Reasoning orchestrator — the deterministic pipeline (Rules 1-5 end to end).

    input codes
      -> facts        (facts.py)
      -> evidence      (evidence.py)
      -> hypotheses    (hypotheses.py)
      -> scoring       (scoring.py)
      -> confidence    (confidence.py)
      -> conflict      (conflict.py)
      -> progression   (progression.py)
      -> differential  (differential.py)
      -> diagnosis     (diagnosis.py)
      -> EngineResult + structured report (rendered to prose ELSEWHERE by an LLM)

No randomness anywhere: identical input always yields identical output.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .confidence import compute_confidence
from .conflict import resolve_conflicts
from .differential import build_differential
from .diagnosis import build_diagnoses
from .evidence import build_evidence
from .facts import build_facts
from .hypotheses import generate_hypotheses
from .models import (
    Confidence, Contradiction, Diagnosis, DifferentialItem, Evidence, Fact,
    Hypothesis, ProgressionPath, ReasoningStep, Resolution, SafetyFlag,
)
from .progression import build_progression
from .recommendations import build_treatment_plan
from .scoring import score_hypotheses


@dataclass(slots=True)
class EngineResult:
    case_id: str
    facts: list[Fact]
    evidence: dict[str, Evidence]
    hypotheses: dict[str, Hypothesis]
    present: list[str]
    tendency: list[str]
    differential: list[DifferentialItem]
    contradictions: list[Contradiction]
    resolutions: list[Resolution]
    progression: ProgressionPath
    diagnoses: list[Diagnosis]
    safety_flags: list[SafetyFlag]
    trace: list[ReasoningStep]
    report: dict = field(default_factory=dict)


class Engine:
    """Loads the knowledge base once; runs deterministic reasoning per case."""

    def __init__(self, data_dir: str | Path):
        d = Path(data_dir)
        self.catalogue: dict[str, dict] = json.loads((d / "evidence.json").read_text())
        self.patterns: list[dict] = json.loads((d / "patterns.json").read_text())["patterns"]
        self.weights: dict = json.loads((d / "weights.json").read_text())
        self.progression_edges: list[dict] = json.loads((d / "progression.json").read_text())["edges"]
        self.conflict_rules: list[dict] = json.loads((d / "conflict_rules.json").read_text())["rules"]
        self.safety_rules: list[dict] = json.loads((d / "rules.json").read_text())["safety"]
        self.nutrition_kb: dict = json.loads((d / "nutrition.json").read_text())

    # -- public API ---------------------------------------------------------
    def run(self, present_codes: list[str], case_id: str = "case") -> EngineResult:
        w = self.weights
        obj_mult = float(w["objective_multiplier"])
        trace: list[ReasoningStep] = []

        facts = build_facts(present_codes, self.catalogue, w["data_confidence"])
        trace.append(ReasoningStep("facts", f"Normalised {len(facts)} present findings into clinical facts."))

        evidence = build_evidence(facts)
        trace.append(ReasoningStep("evidence", f"Elevated {len(evidence)} facts into evidence."))

        hyps = generate_hypotheses(self.patterns, self.catalogue, obj_mult)
        trace.append(ReasoningStep("hypotheses", f"Seeded {len(hyps)} competing pattern hypotheses."))

        links = score_hypotheses(hyps, evidence, self.patterns, obj_mult)
        trace.append(ReasoningStep("scoring", f"Accumulated weighted evidence via {len(links)} graph edges "
                                              f"(objective x{obj_mult:g})."))

        confidences: dict[str, Confidence] = {
            pid: compute_confidence(hyps[pid], w["confidence_weights"], int(w["coverage_target"]),
                                    float(w["diagnosis_threshold"]))
            for pid in hyps
        }
        trace.append(ReasoningStep("confidence", "Computed transparent confidence for every hypothesis."))

        contradictions, resolutions, confidences, suppressed, mixed = resolve_conflicts(
            hyps, confidences, self.conflict_rules, float(w["present_threshold"]),
            float(w["contradiction_penalty"]),
        )
        trace.append(ReasoningStep("conflict", f"Detected {len(contradictions)} contradiction(s); "
                                              f"applied {len(resolutions)} resolution(s)."))

        present = sorted((p for p in hyps if confidences[p].value >= float(w["present_threshold"])
                          and p not in suppressed), key=lambda p: -confidences[p].value)
        tendency = sorted((p for p in hyps
                           if float(w["tendency_threshold"]) <= confidences[p].value < float(w["present_threshold"])
                           and p not in suppressed), key=lambda p: -confidences[p].value)
        active = present + tendency

        progression = build_progression(active, hyps, self.progression_edges)
        trace.append(ReasoningStep("progression", f"Roots: {', '.join(progression.roots) or 'none'}; "
                                                  f"branches: {', '.join(progression.branches) or 'none'}."))

        differential = build_differential(
            hyps, confidences, float(w["present_threshold"]), float(w["tendency_threshold"]),
            suppressed, int(w.get("max_items", 8)),
        )
        trace.append(ReasoningStep("differential", f"Ranked {len(differential)} active hypotheses."))

        diagnoses = build_diagnoses(hyps, confidences, progression, resolutions, suppressed,
                                    float(w["diagnosis_threshold"]))
        trace.append(ReasoningStep("diagnosis", f"Confirmed {len(diagnoses)} diagnosis(es) past the gate "
                                               f"(>= {float(w['diagnosis_threshold']):.0%}, contradictions resolved)."))

        safety = self._safety(present, present_codes, mixed)
        report = self._report(case_id, present, differential, progression, diagnoses, safety, mixed)

        return EngineResult(
            case_id=case_id, facts=facts, evidence=evidence, hypotheses=hyps,
            present=present, tendency=tendency, differential=differential,
            contradictions=contradictions, resolutions=resolutions,
            progression=progression, diagnoses=diagnoses, safety_flags=safety,
            trace=trace, report=report,
        )

    # -- safety guardrails --------------------------------------------------
    def _safety(self, present: list[str], present_codes: list[str], mixed: bool) -> list[SafetyFlag]:
        present_set = set(present)
        codes = set(present_codes)
        out: list[SafetyFlag] = []
        for r in self.safety_rules:
            fire = False
            if "when_any_present" in r and any(x in present_set or x in codes for x in r["when_any_present"]):
                fire = True
            if r.get("when_cold_and_heat") and mixed:
                fire = True
            if "when_all_present" in r:
                ok_all = all(x in present_set for x in r["when_all_present"])
                ok_any = ("when_any_present" not in r) or any(
                    x in present_set or x in codes for x in r.get("when_any_present", []))
                fire = ok_all and ok_any
            if fire:
                out.append(SafetyFlag(rule_id=r["rule_id"], severity=r["severity"], message=r["message"]))
        # de-duplicate, keep highest severity order
        order = {"high": 0, "moderate": 1, "advisory": 2}
        uniq = {f.rule_id: f for f in out}
        return sorted(uniq.values(), key=lambda f: order.get(f.severity, 3))

    # -- structured report (LLM renders this; it performs no reasoning) ------
    def _report(self, case_id, present, differential, progression, diagnoses, safety, mixed) -> dict:
        treatment_plan = build_treatment_plan(diagnoses, self.nutrition_kb)
        return {
            "case_id": case_id,
            "headline": self._headline(diagnoses, present, mixed),
            "root_causes": [d.name for d in diagnoses if d.role == "root"],
            "branches": [d.name for d in diagnoses if d.role == "branch"],
            "diagnoses": [
                {"pattern": d.name, "role": d.role, "confidence": d.confidence.value,
                 "band": d.confidence.band, "priority": d.priority_level,
                 "principle": d.treatment_principle, "formulas": list(d.formulas),
                 "caution": d.caution, "evidence": list(d.evidence), "explanation": d.explanation}
                for d in diagnoses
            ],
            "differential": [
                {"rank": i.rank, "pattern": i.name, "status": i.status,
                 "confidence": i.confidence, "key_evidence": list(i.key_evidence)}
                for i in differential
            ],
            "progression": {
                "roots": list(progression.roots), "branches": list(progression.branches),
                "projected_next": list(progression.projected_next),
                "reversibility": progression.reversibility,
                "mechanisms": [{"from": e.src, "to": e.dst, "relation": e.relation,
                                "mechanism": e.mechanism} for e in progression.edges],
            },
            "safety": [{"severity": f.severity, "message": f.message} for f in safety],
            "mixed_cold_heat": mixed,
            "treatment_plan": treatment_plan,
            "disclaimer": ("Deterministic clinical-reasoning output for practitioner review. "
                           "Not a medical diagnosis; confirm with full examination. Red-flag or "
                           "acute presentations require biomedical referral. Nutrition and herb "
                           "guidance is educational food-therapy information, not a prescription — "
                           "check herb-drug interactions and allergies before use."),
        }

    @staticmethod
    def _headline(diagnoses, present, mixed) -> str:
        if diagnoses:
            roots = [d.name for d in diagnoses if d.role == "root"]
            leads = ", ".join(d.name for d in diagnoses)
            base = f"Confirmed: {leads}."
            if roots:
                base += f" Root: {', '.join(roots)}."
            if mixed:
                base += " Mixed cold-heat — heat likely empty/constrained."
            return base
        if present:
            return "Active patterns present but below the diagnosis threshold; gather more objective signs."
        return "No pattern reached threshold."
