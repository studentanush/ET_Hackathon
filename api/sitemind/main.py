"""SiteMind API — FastAPI over the data spine + agents.

Serves both the JSON API and the single-page dashboard (static/index.html).
Run:  uvicorn sitemind.main:app --reload  (from the api/ dir)
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from . import canonical, crossmodule, db, ingest, repository, seed
from .agents import commissioning, compliance, rag, schedule_risk

app = FastAPI(title="SiteMind API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_STATIC = Path(__file__).resolve().parent / "static"


def conn():
    return db.connect()


# --------------------------------------------------------------------------- #
# dashboard + health
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    return FileResponse(_STATIC / "index.html")


@app.get("/api/health")
def health():
    c = conn()
    try:
        n = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    finally:
        c.close()
    return {"status": "ok", "documents": n, "project": canonical.PROJECT["name"]}


@app.get("/api/dashboard")
def dashboard():
    c = conn()
    try:
        state = schedule_risk.cpm_state(c)
        ncrs = repository.list_ncrs(c)
        risks = repository.list_risk_events(c)
        ships = repository.get_shipments(c)
        at_risk_ships = [s for s in ships if s["status"] in ("delayed", "customs_hold")]
        hours_saved = round(len(ncrs) * 5.5 + 8 * 0.9, 1)  # illustrative aggregate
        return {
            "project": canonical.PROJECT,
            "project_finish": state["project_finish"],
            "critical_path_len": len(state["critical_path"]),
            "open_ncrs": len([n for n in ncrs if n["status"] == "open"]),
            "total_ncrs": len(ncrs),
            "open_risks": len([r for r in risks if r["status"] == "open"]),
            "top_risks": sorted(risks, key=lambda r: (r["impact_days"] or 0) * (r["probability"] or 0),
                                reverse=True)[:3],
            "at_risk_shipments": len(at_risk_ships),
            "documents": repository.list_documents(c),
            "hours_saved": hours_saved,
            "health_score": max(0, 100 - len(risks) * 6 - len([n for n in ncrs if n["status"] == "open"]) * 3),
        }
    finally:
        c.close()


@app.post("/api/reset-demo")
def reset_demo():
    out = seed.run()
    return {"status": "reset", **out}


# --------------------------------------------------------------------------- #
# documents / ingestion
# --------------------------------------------------------------------------- #
@app.get("/api/documents")
def documents(type: str | None = None):
    c = conn()
    try:
        return repository.list_documents(c, type)
    finally:
        c.close()


@app.get("/api/documents/{doc_id}")
def document(doc_id: str):
    c = conn()
    try:
        d = repository.get_document(c, doc_id)
        if not d:
            raise HTTPException(404, "not found")
        d["chunks"] = repository.get_chunks_for_doc(c, doc_id)
        return d
    finally:
        c.close()


class IngestBody(BaseModel):
    doc_id: str
    type: str = "submittal"
    title: str
    content: str
    discipline: str | None = None


@app.post("/api/ingest")
def api_ingest(body: IngestBody):
    c = conn()
    try:
        n = ingest.upsert_document(
            c, doc_id=body.doc_id, doc_type=body.type, title=body.title,
            content=body.content, discipline=body.discipline)
        return {"doc_id": body.doc_id, "chunks": n}
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# compliance
# --------------------------------------------------------------------------- #
class ComplianceBody(BaseModel):
    submittal_doc_id: str


@app.post("/api/compliance/check")
def compliance_check(body: ComplianceBody):
    c = conn()
    try:
        return compliance.check_submittal(c, body.submittal_doc_id)
    finally:
        c.close()


@app.get("/api/compliance/submittals")
def submittals():
    return [{"id": s["id"], "tag": s["equipment_tag"], "spec_section": s["spec_section"],
             "vendor": s["vendor"], "seeded_deviations": len(s["deviations"])}
            for s in canonical.SUBMITTALS]


@app.post("/api/compliance/evaluate")
def compliance_eval(refresh: bool = False):
    c = conn()
    try:
        return compliance.evaluate(c, refresh=refresh)
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# schedule risk
# --------------------------------------------------------------------------- #
@app.get("/api/schedule")
def schedule():
    c = conn()
    try:
        state = schedule_risk.cpm_state(c)
        tasks = repository.get_schedule_tasks(c)
        return {"summary": {k: state[k] for k in ("project_start", "project_finish", "duration_days", "critical_path")},
                "tasks": [{**t, **state["tasks"][t["id"]]} for t in tasks]}
    finally:
        c.close()


@app.post("/api/schedule/analyze")
def schedule_analyze():
    c = conn()
    try:
        return schedule_risk.analyze_risks(c)
    finally:
        c.close()


class WhatIfBody(BaseModel):
    task_id: str
    delay_days: int


@app.post("/api/schedule/what-if")
def schedule_whatif(body: WhatIfBody):
    c = conn()
    try:
        return schedule_risk.what_if(c, body.task_id, body.delay_days)
    finally:
        c.close()


@app.get("/api/schedule/simulation")
def schedule_simulation():
    """Simulation clock: detection-vs-impact timeline for the early-warning story."""
    c = conn()
    try:
        return crossmodule.build_simulation(c)
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# supply chain
# --------------------------------------------------------------------------- #
@app.get("/api/supply/shipments")
def shipments():
    c = conn()
    try:
        out = []
        for s in repository.get_shipments(c):
            at_risk = s["status"] in ("delayed", "customs_hold")
            out.append({**s, "at_risk": at_risk})
        return out
    finally:
        c.close()


@app.post("/api/supply/sync-risks")
def supply_sync():
    """Cross-module hook: at-risk shipments -> schedule risk_events."""
    c = conn()
    try:
        raised = crossmodule.sync_supply_risks(c)
        return {"raised": raised, "count": len(raised)}
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# commissioning
# --------------------------------------------------------------------------- #
@app.get("/api/commissioning/procedures")
def procedures():
    c = conn()
    try:
        return repository.list_test_procedures(c)
    finally:
        c.close()


@app.get("/api/commissioning/readiness")
def readiness():
    """Cross-module hook: schedule risks -> commissioning test readiness."""
    c = conn()
    try:
        return crossmodule.commissioning_readiness(c)
    finally:
        c.close()


class TestBody(BaseModel):
    procedure_id: str
    readings: dict
    executed_by: str = "Cx Engineer"


@app.post("/api/commissioning/validate")
def commissioning_validate(body: TestBody):
    c = conn()
    try:
        return commissioning.validate(c, body.procedure_id, body.readings, executed_by=body.executed_by)
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# knowledge / RFI
# --------------------------------------------------------------------------- #
class AskBody(BaseModel):
    question: str


@app.post("/api/ask")
def ask(body: AskBody):
    c = conn()
    try:
        return rag.ask(c, body.question)
    finally:
        c.close()


@app.post("/api/ask/stream")
def ask_stream(body: AskBody):
    c = conn()
    gen, citations = rag.ask_stream(c, body.question)

    def sse():
        yield f"event: citations\ndata: {json.dumps(citations)}\n\n"
        try:
            for tok in gen:
                yield f"event: token\ndata: {json.dumps(tok)}\n\n"
        finally:
            c.close()
            yield "event: done\ndata: {}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


class RfiBody(BaseModel):
    question: str


@app.post("/api/rfi/draft")
def rfi_draft(body: RfiBody):
    c = conn()
    try:
        return rag.draft_rfi(c, body.question)
    finally:
        c.close()


@app.get("/api/ncrs")
def ncrs():
    c = conn()
    try:
        return repository.list_ncrs(c)
    finally:
        c.close()


@app.get("/api/audit")
def audit():
    c = conn()
    try:
        return repository.list_audit(c)
    finally:
        c.close()
