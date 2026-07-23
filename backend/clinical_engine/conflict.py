"""Conflict layer — detect and deterministically resolve contradictions.

Rule 4: no diagnosis is allowed while contradictions remain unresolved. Here we
detect thermal conflicts (a full-heat pattern competing with a cold pattern) and
resolve them by the objective-over-subjective strategy: whichever side carries
more objective (tongue/pulse/lab) support prevails; if both are objectively
supported and both reach 'present', they are allowed to coexist as a genuinely
mixed picture (and a safety flag is raised elsewhere).
"""
from __future__ import annotations

from .models import Confidence, Contradiction, Hypothesis, Resolution


def _rebuild(conf: Confidence, new_value: float) -> Confidence:
    from .confidence import _band
    v = max(0.0, min(1.0, round(new_value, 4)))
    return Confidence(value=v, band=_band(v), components=conf.components, threshold=conf.threshold)


def resolve_conflicts(
    hyps: dict[str, Hypothesis],
    confidences: dict[str, Confidence],
    conflict_rules: list[dict],
    present_threshold: float,
    penalty: float,
):
    """Return (contradictions, resolutions, adjusted_confidences, suppressed, mixed_cold_heat)."""
    contradictions: list[Contradiction] = []
    resolutions: list[Resolution] = []
    suppressed: set[str] = set()
    adjusted = dict(confidences)
    mixed_cold_heat = False

    active = [pid for pid in sorted(hyps) if confidences[pid].value >= present_threshold - 0.20]

    thermal_rule = next((r for r in conflict_rules if r["type"] == "thermal_conflict"), None)
    if thermal_rule:
        hot = {t for t in thermal_rule["group_a"]}
        cold = {t for t in thermal_rule["group_b"]}
        hot_p = [p for p in active if hyps[p].thermal in hot]
        cold_p = [p for p in active if hyps[p].thermal in cold]
        for a in hot_p:
            for b in cold_p:
                contradictions.append(
                    Contradiction(
                        kind="thermal_conflict", pattern_a=a, pattern_b=b,
                        description=f"{hyps[a].name} (hot) competes with {hyps[b].name} (cold).",
                    )
                )
                a_obj = hyps[a].supporting_objective_weight
                b_obj = hyps[b].supporting_objective_weight
                a_present = confidences[a].value >= present_threshold
                b_present = confidences[b].value >= present_threshold
                if a_obj > 0 and b_obj > 0 and a_present and b_present:
                    mixed_cold_heat = True
                    resolutions.append(Resolution(
                        kind="thermal_conflict", strategy="coexist_complex", status="resolved",
                        winner=None, suppressed=None, coexist=True,
                        explanation=("Both sides objectively supported and present: genuine mixed "
                                     "cold-heat picture — retained as complex, heat likely empty/constrained."),
                    ))
                else:
                    if a_obj >= b_obj:
                        win, lose = a, b
                    else:
                        win, lose = b, a
                    suppressed.add(lose)
                    adjusted[lose] = _rebuild(adjusted[lose], adjusted[lose].value - penalty)
                    # a cold+heat coexistence at tendency level is still a mixed signal
                    mixed_cold_heat = mixed_cold_heat or (a_obj > 0 and b_obj > 0)
                    resolutions.append(Resolution(
                        kind="thermal_conflict", strategy="objective_over_subjective", status="resolved",
                        winner=win, suppressed=lose, coexist=False,
                        explanation=(f"{hyps[win].name} retained (objective support "
                                     f"{max(a_obj, b_obj):.1f} vs {min(a_obj, b_obj):.1f}); "
                                     f"{hyps[lose].name} suppressed as branch/artefact."),
                    ))
    return contradictions, resolutions, adjusted, suppressed, mixed_cold_heat
