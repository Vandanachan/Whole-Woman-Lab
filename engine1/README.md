# WholeWomanLab — Engine 1: Clinical Reasoning Engine

A **deterministic, explainable** clinical-reasoning engine. Diagnosis is produced
**only** by rules and weighted evidence — there is no LLM inference anywhere in
this package. (An LLM is used *elsewhere*, in the Report engine, purely to render
the structured output below into human prose.)

Runs on Python 3.11+ (targets 3.12). Zero heavy dependencies for the core:
standard library only. `pytest` for the test suite.

## Quick start

```bash
cd engine1
python app.py                     # runs the built-in sample case
python app.py TONGUE_RED PULSE_THIN KNOWN_YIN_DEF   # or your own finding codes
python -m pytest tests/ -q        # 9 behavioural tests
```

## The pipeline (Rules 1–5)

```
present finding codes
   -> facts.py         normalise into immutable ClinicalFacts      (Rule 1: everything is evidence)
   -> evidence.py      lift facts into indexed Evidence
   -> hypotheses.py    seed one competing Hypothesis per pattern    (Rule 2: evidence -> hypotheses)
   -> scoring.py       weighted accumulation; objective x3          (Rule 3: hypotheses compete)
   -> confidence.py    transparent, bounded confidence per pattern
   -> conflict.py      detect + resolve contradictions              (Rule 4: resolve before diagnosing)
   -> progression.py   root vs branch + where it is heading
   -> differential.py  rank the active hypotheses
   -> diagnosis.py     gate: confidence>=threshold AND no unresolved
                        contradiction, else no diagnosis            (Rule 4 + Rule 5: explainable)
   -> reasoning.py     orchestrates all of the above -> EngineResult + structured report
```

### The five rules, enforced structurally
1. **Everything is evidence.** Inputs normalise to `Fact` then `Evidence`; neither is a diagnosis.
2. **Evidence generates hypotheses.** Every catalogue pattern is seeded and competes.
3. **Hypotheses compete.** Each finding strengthens/weakens patterns via weighted edges;
   objective findings (tongue/pulse/labs/confirmed history) are weighted **3×** symptoms.
4. **No diagnosis unless confidence ≥ threshold AND contradictions resolved.** Enforced in
   `diagnosis.py`; a case with unresolved conflict or thin evidence returns **no** diagnosis.
5. **Every diagnosis is explainable.** Each `Diagnosis` carries evidence, role (root/branch),
   confidence (with component breakdown), priority and a written explanation.

## Layout

```
engine1/
├── app.py                  # demo runner / CLI
├── engine/
│   ├── models.py           # dataclasses: Fact, Evidence, Hypothesis, Diagnosis, …
│   ├── facts.py            # normalisation
│   ├── evidence.py         # evidence indexing
│   ├── hypotheses.py       # hypothesis seeding + max-possible
│   ├── scoring.py          # deterministic weighted scoring + graph edges
│   ├── confidence.py       # transparent confidence
│   ├── conflict.py         # contradiction detection + resolution
│   ├── progression.py      # root/branch + progression graph
│   ├── differential.py     # ranking
│   ├── diagnosis.py        # the Rule 4/5 gate
│   └── reasoning.py        # orchestrator -> EngineResult + structured report
├── data/
│   ├── evidence.json       # 75 finding codes (label/modality/type/objective)
│   ├── patterns.json       # 8 TCM patterns + expected evidence weights
│   ├── weights.json        # thresholds, objective multiplier, confidence weights
│   ├── progression.json    # pattern-progression edges (root/branch, "heading to")
│   ├── conflict_rules.json # thermal & excess/deficiency conflict handling
│   └── rules.json          # safety guardrails (e.g. no-warming for yin/blood def)
├── tests/                  # pytest suite (9 tests)
└── README.md
```

## Extending the knowledge base

All clinical content lives in `data/*.json` — **no code changes needed** to add
patterns or findings:

* **Add a finding**: new entry in `evidence.json` (`objective: true` for tongue/pulse/labs).
* **Add a pattern**: append to `patterns.json` with its `expected_evidence` (code + weight).
* **Tune behaviour**: `weights.json` (`objective_multiplier`, `present_threshold`,
  `diagnosis_threshold`, `confidence_weights`).
* **Progression / conflicts / safety**: `progression.json`, `conflict_rules.json`, `rules.json`.

## Output contract (for the Report engine / LLM renderer)

`EngineResult.report` is a plain dict with: `headline`, `root_causes`, `branches`,
`diagnoses[]`, `differential[]`, `progression{}`, `safety[]`, `mixed_cold_heat`,
`disclaimer`. The LLM renderer consumes this verbatim and **only formats it** — it
never re-reasons.

## Where this sits in the 5-engine system

| # | Engine | Consumes | Produces |
|---|--------|----------|----------|
| **1** | **Clinical Reasoning** (this) | finding codes | patterns, roots, differential, safety |
| 2 | Adaptive Intake | engine-1 confidence gaps | the next best question to ask |
| 3 | Integrative Diagnosis | 1 + tongue/lab/HTMA modules | cross-system reconciled picture |
| 4 | Recommendation | 3 + safety flags | nutrition/herbs/lifestyle + contraindication checks |
| 5 | Report Generation | 1–4 | human-readable, PDF-ready report |

Engine 2 plugs directly into the confidence layer here: any pattern sitting in the
`tendency` band with high information-gain findings still unobserved becomes the
next question. That interface is already present (`EngineResult.tendency` +
per-hypothesis `unmet_expected`).
