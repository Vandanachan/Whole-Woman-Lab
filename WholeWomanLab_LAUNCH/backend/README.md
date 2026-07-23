# WholeWomanLab — Backend API

FastAPI service that serves the intake questionnaire, runs **Engine 1** (the
deterministic clinical-reasoning engine, vendored under `clinical_engine/`) on
submitted answers, and returns either a structured JSON reading or a generated
**PDF report**. No LLM is involved in the reasoning; the engine is fully
deterministic.

## Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
#   or:  ./run.sh
```

Open the interactive docs at **http://localhost:8000/docs** (Swagger UI, built in).

## Endpoints

| Method | Path           | Purpose |
|--------|----------------|---------|
| GET    | `/health`      | liveness probe |
| GET    | `/questions`   | intake schema (checklists of finding-codes), built from the engine catalogue |
| POST   | `/diagnose`    | run Engine 1 -> structured report JSON |
| POST   | `/report/pdf`  | run Engine 1 -> generated PDF (`application/pdf`) |

### Request body (`/diagnose`, `/report/pdf`)

```json
{
  "codes": ["KNOWN_YIN_DEF", "TONGUE_RED", "TONGUE_CENTRAL_CRACK", "PULSE_THIN", "..."],
  "client": { "name": "Jane", "age": 34, "sex": "Female" },
  "case_id": "jane-2025-07"
}
```

`codes` is simply the list of finding-codes the client/practitioner selected in
the questionnaire. Unknown codes -> `400`.

### Try it from the command line

```bash
# structured reading
curl -s localhost:8000/diagnose -H 'content-type: application/json' \
  -d '{"codes":["KNOWN_YIN_DEF","TONGUE_RED","TONGUE_CENTRAL_CRACK","PULSE_THIN","IRRITABILITY","SIGHING"]}' | jq .report.headline

# download the PDF
curl -s localhost:8000/report/pdf -H 'content-type: application/json' \
  -d '{"codes":["KNOWN_YIN_DEF","TONGUE_RED","TONGUE_CENTRAL_CRACK","PULSE_THIN"]}' -o report.pdf
```

## Tests

```bash
cd backend
pytest -q          # 6 API tests (health, questions, diagnose, safety, pdf, unknown-code)
```

## How a frontend uses this

1. `GET /questions` -> render checklists; each option has a `code`.
2. User ticks findings -> collect the selected `code`s.
3. `POST /diagnose` -> show the on-screen reading, **or**
   `POST /report/pdf` -> offer a "Download report" button (the response *is* the PDF).

CORS is open (`*`) for local development — **restrict `allow_origins` before
deploying**.

## Project layout

```
backend/
├── app/
│   ├── main.py            # FastAPI app + routes
│   ├── schemas.py         # request/response models
│   ├── engine_bridge.py   # loads Engine 1, validates + runs
│   ├── question_bank.py   # builds intake schema from the engine catalogue
│   └── pdf_report.py      # fpdf2 PDF builder (formats only; no reasoning)
├── clinical_engine/       # vendored Engine 1 (deterministic reasoning)
├── data/                  # vendored knowledge base (evidence/patterns/rules/…)
├── tests/                 # pytest API suite
├── requirements.txt
└── run.sh
```

## Deploying (when you're ready)

* **Render / Railway / Fly.io**: point at this folder, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Free/starter tiers are fine
  to begin.
* Add a database (Postgres) only when you want to *store* client responses; the
  API itself is stateless and needs none to run.
* This handles health-adjacent data — restrict CORS, add auth, and review privacy
  obligations before going live with real clients.
```
