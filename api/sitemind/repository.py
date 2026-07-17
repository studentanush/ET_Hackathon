"""Data-access layer.

Every DB read/write goes through here so the storage engine (SQLite+numpy today,
pgvector tomorrow) is a single swap point. Agents call these helpers via tools;
they never touch SQL directly.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

import numpy as np

from . import db, embeddings


# --------------------------------------------------------------------------- #
# generic helpers
# --------------------------------------------------------------------------- #
def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _row(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> dict | None:
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def _json(val: Any, default):
    if val in (None, ""):
        return default
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default


# --------------------------------------------------------------------------- #
# vector search (brute-force cosine; vectors are unit-normalized)
# --------------------------------------------------------------------------- #
def vector_search(
    conn: sqlite3.Connection,
    query: str,
    *,
    k: int = 6,
    doc_types: list[str] | None = None,
    section: str | None = None,
) -> list[dict]:
    """Return top-k chunks by cosine similarity, with optional metadata filters.

    Combines dense similarity with a light lexical bonus (keyword overlap) — a
    cheap stand-in for the hybrid vector+BM25 retrieval in the plan.
    """
    where = ["c.embedding IS NOT NULL"]
    params: list[Any] = []
    if doc_types:
        where.append(f"d.type IN ({','.join('?' * len(doc_types))})")
        params += doc_types
    if section:
        where.append("c.section_ref LIKE ?")
        params.append(f"%{section}%")
    sql = (
        "SELECT c.id, c.document_id, c.seq, c.text, c.embedding, c.page, "
        "c.section_ref, d.title, d.type, d.discipline "
        "FROM chunks c JOIN documents d ON d.id = c.document_id "
        f"WHERE {' AND '.join(where)}"
    )
    rows = conn.execute(sql, tuple(params)).fetchall()
    if not rows:
        return []

    qv = embeddings.embed_one(query)
    mat = np.stack([embeddings.from_blob(r["embedding"]) for r in rows])
    sims = mat @ qv  # unit vectors -> dot product == cosine

    q_terms = {w for w in query.lower().split() if len(w) > 3}
    out = []
    for r, s in zip(rows, sims):
        lex = 0.0
        if q_terms:
            text_l = (r["text"] or "").lower()
            hits = sum(1 for t in q_terms if t in text_l)
            lex = 0.05 * hits
        d = dict(r)
        d.pop("embedding", None)
        d["score"] = float(s) + lex
        out.append(d)
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:k]


# --------------------------------------------------------------------------- #
# documents / chunks
# --------------------------------------------------------------------------- #
def get_document(conn, doc_id: str) -> dict | None:
    return _row(conn, "SELECT * FROM documents WHERE id = ?", (doc_id,))


def list_documents(conn, doc_type: str | None = None) -> list[dict]:
    if doc_type:
        return _rows(conn, "SELECT * FROM documents WHERE type = ? ORDER BY id", (doc_type,))
    return _rows(conn, "SELECT * FROM documents ORDER BY type, id")


def get_chunks_for_doc(conn, doc_id: str) -> list[dict]:
    rows = _rows(
        conn,
        "SELECT id, document_id, seq, text, page, section_ref FROM chunks "
        "WHERE document_id = ? ORDER BY seq",
        (doc_id,),
    )
    return rows


# --------------------------------------------------------------------------- #
# specs / compliance support
# --------------------------------------------------------------------------- #
def get_spec_clauses(conn, section: str, *, k: int = 12) -> list[dict]:
    """Fetch clause chunks for a spec section (metadata-filtered, ordered)."""
    rows = _rows(
        conn,
        "SELECT c.id, c.document_id, c.seq, c.text, c.page, c.section_ref, d.title "
        "FROM chunks c JOIN documents d ON d.id = c.document_id "
        "WHERE d.type = 'spec' AND (c.section_ref LIKE ? OR d.title LIKE ?) "
        "ORDER BY c.seq LIMIT ?",
        (f"%{section}%", f"%{section}%", k),
    )
    return rows


# --------------------------------------------------------------------------- #
# line items / procurement / shipments
# --------------------------------------------------------------------------- #
def get_line_item(conn, item_id: str) -> dict | None:
    return _row(conn, "SELECT * FROM line_items WHERE id = ? OR tag = ?", (item_id, item_id))


def get_procurement_status(conn) -> list[dict]:
    return _rows(
        conn,
        "SELECT po.*, li.tag, li.description, li.criticality "
        "FROM procurement_orders po LEFT JOIN line_items li ON li.id = po.line_item_id "
        "ORDER BY po.promised_date",
    )


def get_shipments(conn) -> list[dict]:
    return _rows(
        conn,
        "SELECT s.*, po.vendor, po.line_item_id FROM shipments s "
        "LEFT JOIN procurement_orders po ON po.id = s.po_id ORDER BY s.eta",
    )


# --------------------------------------------------------------------------- #
# schedule
# --------------------------------------------------------------------------- #
def get_schedule_tasks(conn) -> list[dict]:
    rows = _rows(conn, "SELECT * FROM schedule_tasks ORDER BY wbs")
    for r in rows:
        r["predecessors"] = _json(r.get("predecessors"), [])
        r["is_critical"] = bool(r.get("is_critical"))
    return rows


# --------------------------------------------------------------------------- #
# NCRs
# --------------------------------------------------------------------------- #
def create_ncr(conn, ncr: dict) -> dict:
    conn.execute(
        "INSERT OR REPLACE INTO ncrs "
        "(id, source_module, severity, description, spec_citation, equipment_tag, status, raised_at) "
        "VALUES (:id,:source_module,:severity,:description,:spec_citation,:equipment_tag,:status,:raised_at)",
        {
            "status": "open",
            "spec_citation": "",
            "equipment_tag": "",
            **ncr,
        },
    )
    conn.commit()
    log(conn, "system", "create", "ncr", ncr["id"], ncr)
    return get_ncr(conn, ncr["id"])


def get_ncr(conn, ncr_id: str) -> dict | None:
    return _row(conn, "SELECT * FROM ncrs WHERE id = ?", (ncr_id,))


def list_ncrs(conn, status: str | None = None) -> list[dict]:
    if status:
        return _rows(conn, "SELECT * FROM ncrs WHERE status = ? ORDER BY raised_at DESC", (status,))
    return _rows(conn, "SELECT * FROM ncrs ORDER BY raised_at DESC")


# --------------------------------------------------------------------------- #
# RFIs
# --------------------------------------------------------------------------- #
def list_rfis(conn) -> list[dict]:
    rows = _rows(conn, "SELECT * FROM rfis ORDER BY number")
    for r in rows:
        r["spec_refs"] = _json(r.get("spec_refs"), [])
    return rows


def find_similar_rfis(conn, text: str, *, k: int = 4) -> list[dict]:
    """Embedding similarity over answered RFI question text."""
    rfis = _rows(
        conn, "SELECT * FROM rfis WHERE answer IS NOT NULL AND answer != ''"
    )
    if not rfis:
        return []
    qv = embeddings.embed_one(text)
    mat = embeddings.embed([r["question"] for r in rfis])
    sims = mat @ qv
    scored = []
    for r, s in zip(rfis, sims):
        r["similarity"] = float(s)
        r["spec_refs"] = _json(r.get("spec_refs"), [])
        scored.append(r)
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:k]


# --------------------------------------------------------------------------- #
# risk events
# --------------------------------------------------------------------------- #
def create_risk_event(conn, ev: dict) -> dict:
    payload = {
        "probability": 0.5,
        "impact_days": 0,
        "affected_tasks": "[]",
        "mitigation_options": "[]",
        "status": "open",
        "title": "",
        "description": "",
        "risk_type": "generic",
        **ev,
    }
    if isinstance(payload["affected_tasks"], list):
        payload["affected_tasks"] = json.dumps(payload["affected_tasks"])
    if isinstance(payload["mitigation_options"], (list, dict)):
        payload["mitigation_options"] = json.dumps(payload["mitigation_options"])
    conn.execute(
        "INSERT OR REPLACE INTO risk_events "
        "(id, source_module, risk_type, title, description, probability, impact_days, "
        " affected_tasks, detected_at, mitigation_options, status) "
        "VALUES (:id,:source_module,:risk_type,:title,:description,:probability,:impact_days,"
        ":affected_tasks,:detected_at,:mitigation_options,:status)",
        payload,
    )
    conn.commit()
    return get_risk_event(conn, ev["id"])


def get_risk_event(conn, rid: str) -> dict | None:
    r = _row(conn, "SELECT * FROM risk_events WHERE id = ?", (rid,))
    if r:
        r["affected_tasks"] = _json(r.get("affected_tasks"), [])
        r["mitigation_options"] = _json(r.get("mitigation_options"), [])
    return r


def list_risk_events(conn) -> list[dict]:
    rows = _rows(conn, "SELECT * FROM risk_events ORDER BY impact_days DESC")
    for r in rows:
        r["affected_tasks"] = _json(r.get("affected_tasks"), [])
        r["mitigation_options"] = _json(r.get("mitigation_options"), [])
    return rows


# --------------------------------------------------------------------------- #
# test procedures / records
# --------------------------------------------------------------------------- #
def list_test_procedures(conn) -> list[dict]:
    rows = _rows(conn, "SELECT * FROM test_procedures ORDER BY level, id")
    for r in rows:
        r["acceptance_criteria"] = _json(r.get("acceptance_criteria"), [])
    return rows


def get_test_procedure(conn, pid: str) -> dict | None:
    r = _row(conn, "SELECT * FROM test_procedures WHERE id = ?", (pid,))
    if r:
        r["acceptance_criteria"] = _json(r.get("acceptance_criteria"), [])
    return r


def save_test_record(conn, rec: dict) -> dict:
    payload = {"ncr_id": None, **rec}
    if isinstance(payload.get("readings"), (list, dict)):
        payload["readings"] = json.dumps(payload["readings"])
    conn.execute(
        "INSERT OR REPLACE INTO test_records "
        "(id, procedure_id, executed_by, executed_at, readings, result, ncr_id) "
        "VALUES (:id,:procedure_id,:executed_by,:executed_at,:readings,:result,:ncr_id)",
        payload,
    )
    conn.commit()
    return _row(conn, "SELECT * FROM test_records WHERE id = ?", (rec["id"],))


# --------------------------------------------------------------------------- #
# audit
# --------------------------------------------------------------------------- #
def log(conn, actor: str, action: str, entity: str, entity_id: str, detail: Any) -> None:
    from datetime import datetime, timezone

    conn.execute(
        "INSERT INTO audit_log (actor, action, entity, entity_id, detail, at) "
        "VALUES (?,?,?,?,?,?)",
        (actor, action, entity, entity_id, json.dumps(detail, default=str),
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def list_audit(conn, limit: int = 50) -> list[dict]:
    rows = _rows(conn, "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    for r in rows:
        r["detail"] = _json(r.get("detail"), {})
    return rows
