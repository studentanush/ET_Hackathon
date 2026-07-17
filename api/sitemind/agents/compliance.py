"""Spec & Quality Compliance Agent (flagship #1).

Flow: submittal -> retrieve governing spec clauses -> structured clause-by-clause
verdict (LLM, JSON mode) -> auto-create NCRs for deviations -> emit a risk_event
if the item is on the critical path (the cross-module hook).
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import canonical, db, llm, repository
from ..schemas import ComplianceReport

SYS = (
    "You are a senior data-centre commissioning & QA engineer reviewing a vendor "
    "submittal against the governing specification for an EPC project. Compare EACH "
    "spec clause to the submitted value.\n"
    "- COMPLIANT: the submitted value meets or exceeds the requirement.\n"
    "- DEVIATION: the submitted value fails the requirement, OR a MANDATORY item "
    "(seismic certification, type-test certificate, factory witness test, N+1 "
    "redundancy) is 'not provided'/'not stated'/False — a missing mandatory "
    "requirement is a non-conformance, NOT 'unclear'.\n"
    "- UNCLEAR: only when a NON-mandatory value is genuinely ambiguous.\n"
    "For tolerance/operating-window requirements stated as 'at least +/-X%', a WIDER "
    "window is COMPLIANT (e.g. +/-20% satisfies a +/-15% requirement) and a NARROWER "
    "window is a DEVIATION (e.g. +/-10% fails +/-15%).\n"
    "Set severity from the clause (minor/major/critical). Cite the clause ref and "
    "spec doc id. A single DEVIATION makes summary_verdict NON_COMPLIANT."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compare(conn, submittal_doc_id: str, *, effort: str = "high") -> ComplianceReport:
    """Read-only: retrieve the governing spec and produce the verdict. No DB writes.

    Used both by check_submittal (which then persists) and by the evaluation
    harness (which must not pollute the NCR register)."""
    doc = repository.get_document(conn, submittal_doc_id)
    if not doc:
        raise ValueError(f"Unknown submittal {submittal_doc_id}")

    # Identify the governing spec section from the submittal metadata/content.
    section = _infer_section(conn, submittal_doc_id, doc)
    spec_chunks = repository.get_spec_clauses(conn, section)
    spec_text = "\n".join(f"[{c['section_ref']}] {c['text']}" for c in spec_chunks)

    user = (
        f"GOVERNING SPEC SECTION {section}:\n{spec_text}\n\n"
        f"VENDOR SUBMITTAL ({submittal_doc_id}, doc title '{doc['title']}'):\n{doc['content']}\n\n"
        "Produce the compliance report. Use doc_id "
        f"'SPEC-{section.replace(' ', '')}' for spec citations."
    )
    return llm.complete_json(
        [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
        ComplianceReport,
        effort=effort,
        temperature=0.0,
    )


def check_submittal(conn, submittal_doc_id: str, *, effort: str = "high") -> dict:
    report = compare(conn, submittal_doc_id, effort=effort)
    ncrs, risk = _apply_findings(conn, report)
    repository.log(conn, "compliance-agent", "check", "submittal", submittal_doc_id,
                   {"verdict": report.summary_verdict, "ncrs": [n["id"] for n in ncrs]})
    return {"report": report.model_dump(), "ncrs": ncrs, "risk_event": risk}


def _infer_section(conn, doc_id: str, doc: dict) -> str:
    for sub in canonical.SUBMITTALS:
        if sub["id"] == doc_id:
            return sub["spec_section"]
    # Fallback: match any known section string appearing in the content.
    for section in canonical.SPECS:
        if section in (doc.get("content") or ""):
            return section
    return next(iter(canonical.SPECS))


def _apply_findings(conn, report: ComplianceReport):
    """Deviations -> NCR rows; a critical-path item -> risk_event (cross-module)."""
    ncrs = []
    deviations = [f for f in report.findings if f.verdict == "DEVIATION"]
    tag = report.equipment_tag
    for i, f in enumerate(deviations, 1):
        ncr_id = f"NCR-{tag}-{f.clause_ref}".replace(" ", "").replace("/", "-")
        ncr = repository.create_ncr(conn, {
            "id": ncr_id,
            "source_module": "compliance",
            "severity": f.severity if f.severity != "none" else "major",
            "description": f"{f.requirement} — submitted: {f.submittal_value}. {f.recommended_action}",
            "spec_citation": f"{report.spec_section} / {f.clause_ref}",
            "equipment_tag": tag,
            "raised_at": _now(),
        })
        ncrs.append(ncr)

    risk = None
    if deviations and tag in canonical.CRITICAL_TAGS:
        # Rejection forces a resubmittal + refab cycle on a critical-path item.
        affected = _tasks_for_tag(conn, tag)
        risk = repository.create_risk_event(conn, {
            "id": f"RISK-{tag}-COMPLIANCE",
            "source_module": "compliance",
            "risk_type": "resubmittal_leadtime",
            "title": f"{tag} submittal rejected on a critical-path item",
            "description": (
                f"{tag} is non-compliant ({len(deviations)} deviation(s)). Rejection triggers a "
                "resubmittal + re-manufacture cycle on the critical path, threatening the "
                "energization and integrated-test window."),
            "probability": 0.8,
            "impact_days": 21,
            "affected_tasks": affected,
            "detected_at": _now(),
            "status": "open",
        })
    return ncrs, risk


def _tasks_for_tag(conn, tag: str) -> list[str]:
    if tag == "SWGR-MV-01":
        return ["T-021", "T-022", "T-023", "T-070"]
    return []


# --------------------------------------------------------------------------- #
# Evaluation harness: precision / recall vs labelled deviations (plan §2, §6.1)
# --------------------------------------------------------------------------- #
import json as _json
from pathlib import Path as _Path

_EVAL_CACHE = _Path(__file__).resolve().parent.parent.parent / "eval_cache.json"


def evaluate(conn, *, effort: str = "high", refresh: bool = False) -> dict:
    """Return the compliance accuracy result over the labelled test set.

    Each run is 9 reasoning-model calls (~2 min on Groq's free tier, which
    serialises concurrent reasoning requests), so the result is CACHED. The demo
    button returns the cached numbers instantly; pass refresh=True to recompute
    live. The cached numbers are real — produced by this same code path.
    """
    if not refresh and _EVAL_CACHE.exists():
        try:
            cached = _json.loads(_EVAL_CACHE.read_text())
            cached["cached"] = True
            return cached
        except (ValueError, OSError):
            pass
    result = _compute_eval(effort=effort)
    result["cached"] = False
    try:
        _EVAL_CACHE.write_text(_json.dumps(result, indent=2))
    except OSError:
        pass
    return result


def _compute_eval(*, effort: str = "high") -> dict:
    """Run every canonical submittal (read-only) and compare to ground truth.
    Resilient: a failed call yields no findings rather than crashing the run."""
    from concurrent.futures import ThreadPoolExecutor

    def _worker(sub: dict):
        c = db.connect()
        try:
            for attempt in range(3):  # retry transient rate-limit / network errors
                try:
                    return {"sub": sub, "report": compare(c, sub["id"], effort=effort)}
                except Exception:
                    if attempt == 2:
                        return {"sub": sub, "report": None}
        finally:
            c.close()

    # Sequential — Groq's free tier rate-limits concurrent reasoning calls, which
    # would spuriously fail some checks. This runs offline to build the cache, so
    # reliability matters more than speed.
    with ThreadPoolExecutor(max_workers=1) as pool:
        results = list(pool.map(_worker, canonical.SUBMITTALS))

    tp = fp = fn = 0
    per_doc = []
    for r in results:
        sub, report = r["sub"], r["report"]
        truth = {d["clause_ref"] for d in sub["deviations"]}
        found = ({f.clause_ref for f in report.findings if f.verdict == "DEVIATION"}
                 if report else set())
        d_tp = len(truth & found)
        d_fp = len(found - truth)
        d_fn = len(truth - found)
        tp += d_tp; fp += d_fp; fn += d_fn
        per_doc.append({
            "submittal": sub["id"], "tag": sub["equipment_tag"],
            "expected": sorted(truth), "flagged": sorted(found),
            "tp": d_tp, "fp": d_fp, "fn": d_fn,
            "verdict": report.summary_verdict if report else "ERROR",
        })
    per_doc.sort(key=lambda x: x["submittal"])
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "true_positives": tp, "false_positives": fp, "false_negatives": fn,
        "per_document": per_doc,
    }
