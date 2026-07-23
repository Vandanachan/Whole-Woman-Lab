"""End-to-end API tests using FastAPI's TestClient (no live server needed)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE = [
    "KNOWN_YIN_DEF", "KNOWN_BLOOD_DEF",
    "TONGUE_RED", "TONGUE_CENTRAL_CRACK", "TONGUE_TIP_RED", "TONGUE_SIDES_RED",
    "PULSE_THIN", "PULSE_RAPID", "PULSE_WIRY", "PULSE_WEAK",
    "DRY_EYES_SKIN", "WAKE_1_3AM", "STOOL_DRY_FRAGMENTED", "STOOL_LOOSE",
    "STOOL_MUCUS", "STOOL_ALTERNATING", "GAS_BLOATING", "IRRITABILITY",
    "SIGHING", "WORSE_STRESS", "COLD_LIMBS", "FATIGUE",
]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["codes"] > 0


def test_questions_schema():
    r = client.get("/questions")
    assert r.status_code == 200
    body = r.json()
    assert body["total_codes"] > 0
    keys = {s["key"] for s in body["sections"]}
    assert {"symptom", "tongue", "pulse", "history"} <= keys
    # every option carries a code + label
    for s in body["sections"]:
        for o in s["options"]:
            assert o["code"] and o["label"]


def test_diagnose_surfaces_yin_and_safety():
    r = client.post("/diagnose", json={"codes": SAMPLE, "client": {"name": "Test", "age": 24, "sex": "Female"}})
    assert r.status_code == 200
    body = r.json()
    dx = {d["pattern"] for d in body["report"]["diagnoses"]}
    assert "Yin Deficiency" in dx
    safety_msgs = " ".join(s["message"] for s in body["report"]["safety"])
    assert "do NOT use strong warming" in safety_msgs
    assert "TCM_YIN_XU" in body["present"]


def test_diagnose_rejects_unknown_code():
    r = client.post("/diagnose", json={"codes": ["NONSENSE_CODE"]})
    assert r.status_code == 400
    assert "Unknown finding codes" in r.json()["detail"]


def test_pdf_generation():
    r = client.post("/report/pdf", json={"codes": SAMPLE, "client": {"name": "Test Client", "age": 24}})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"
    assert len(r.content) > 1500  # a real, non-trivial document


def test_pdf_empty_case_still_valid():
    r = client.post("/report/pdf", json={"codes": ["FATIGUE"]})
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"
