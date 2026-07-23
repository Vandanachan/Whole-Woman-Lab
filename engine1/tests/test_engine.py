"""Engine 1 behavioural tests — proves the reasoning is correct & deterministic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.reasoning import Engine

DATA = Path(__file__).resolve().parents[1] / "data"

SAMPLE = [
    "KNOWN_YIN_DEF", "KNOWN_BLOOD_DEF",
    "TONGUE_RED", "TONGUE_CENTRAL_CRACK", "TONGUE_TIP_RED", "TONGUE_SIDES_RED",
    "PULSE_THIN", "PULSE_RAPID", "PULSE_WIRY", "PULSE_WEAK",
    "DRY_EYES_SKIN", "TIRED_WIRED", "WAKE_1_3AM",
    "STOOL_DRY_FRAGMENTED", "STOOL_LOOSE", "STOOL_MUCUS", "STOOL_ALTERNATING",
    "GAS_BLOATING", "IRRITABILITY", "SIGHING", "WORSE_STRESS",
    "COLD_LIMBS", "FATIGUE",
]


@pytest.fixture(scope="module")
def engine() -> Engine:
    return Engine(DATA)


def test_yin_deficiency_is_surfaced_not_buried(engine):
    """The core failure mode we designed against: yin-def must not be missed."""
    res = engine.run(SAMPLE)
    assert "TCM_YIN_XU" in res.present, "Yin deficiency should be a present pattern"
    dx_ids = {d.pattern_id for d in res.diagnoses}
    assert "TCM_YIN_XU" in dx_ids, "Yin deficiency should reach a confirmed diagnosis"


def test_blood_deficiency_and_stagnation_present(engine):
    res = engine.run(SAMPLE)
    assert "TCM_XUE_XU" in res.present
    assert "TCM_QI_ZHI" in res.present


def test_yang_deficiency_not_over_called(engine):
    """Objective heat signs must stop yang-deficiency being a confirmed diagnosis."""
    res = engine.run(SAMPLE)
    dx_ids = {d.pattern_id for d in res.diagnoses}
    assert "TCM_YANG_XU" not in dx_ids


def test_no_warming_guardrail_fires(engine):
    res = engine.run(SAMPLE)
    ids = {f.rule_id for f in res.safety_flags}
    assert "SAFE_NO_WARM_DRY" in ids, "Must warn against warming a yin/blood-deficient client"


def test_root_vs_branch(engine):
    res = engine.run(SAMPLE)
    # qi-stagnation and the deficiencies are eligible roots; stasis/heat are branches
    assert res.progression.roots, "Expected at least one root pattern"
    assert "TCM_QI_ZHI" in res.progression.roots or "TCM_YIN_XU" in res.progression.roots


def test_diagnosis_gate_threshold(engine):
    """A thin, low-signal case yields no confirmed diagnosis (Rule 4)."""
    res = engine.run(["FATIGUE", "GAS_BLOATING"])
    assert res.diagnoses == [], "Weak evidence must not produce a confirmed diagnosis"


def test_unknown_code_rejected(engine):
    with pytest.raises(KeyError):
        engine.run(["NOT_A_REAL_CODE"])


def test_determinism(engine):
    """Identical input -> byte-identical structured report."""
    a = json.dumps(engine.run(SAMPLE).report, sort_keys=True)
    b = json.dumps(engine.run(SAMPLE).report, sort_keys=True)
    assert a == b


def test_every_diagnosis_is_explainable(engine):
    """Rule 5: evidence + confidence + priority + explanation always present."""
    res = engine.run(SAMPLE)
    for d in res.diagnoses:
        assert d.evidence, "diagnosis must cite evidence"
        assert d.explanation.strip()
        assert 0.0 <= d.confidence.value <= 1.0
        assert d.priority_level in {"monitor", "routine", "moderate", "high", "urgent"}
