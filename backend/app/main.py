"""WholeWomanLab backend API.

Endpoints
---------
GET  /health          liveness probe
GET  /questions       intake schema (built from the engine's finding catalogue)
POST /diagnose        run Engine 1 on submitted finding-codes -> structured report
POST /report/pdf      same, but returns a generated PDF report

The reasoning is 100% deterministic (Engine 1). No LLM is involved here.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import engine_bridge as bridge
from app.pdf_report import build_pdf
from app.question_bank import build_schema
from app.schemas import DiagnoseRequest, QuestionsResponse

app = FastAPI(
    title="Whole Woman Lab — Clinical Intelligence API",
    version="1.0.0",
    description="Deterministic clinical-reasoning engine (Engine 1) with PDF reporting.",
)

# permissive CORS for local frontend development; tighten allow_origins in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "clinical-reasoning-1", "codes": len(bridge.known_codes())}


@app.get("/questions", response_model=QuestionsResponse)
def questions() -> QuestionsResponse:
    schema = build_schema(bridge.catalogue())
    total = sum(len(s["options"]) for s in schema)
    return QuestionsResponse(sections=schema, total_codes=total)


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest) -> JSONResponse:
    try:
        result = bridge.run(req.codes, case_id=req.case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(
        {
            "report": result.report,
            "present": result.present,
            "tendency": result.tendency,
            "trace": [{"stage": s.stage, "description": s.description} for s in result.trace],
        }
    )


@app.post("/report/pdf")
def report_pdf(req: DiagnoseRequest) -> Response:
    try:
        result = bridge.run(req.codes, case_id=req.case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    client = req.client.model_dump() if req.client else None
    pdf_bytes = build_pdf(result.report, client)
    fname = f"wwl_report_{req.case_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{fname}"'},
    )
