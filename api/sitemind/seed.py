"""Seed the SQLite spine from canonical.py — the known-good demo snapshot.

Run:  python -m sitemind.seed
Rebuilds the DB deterministically: specs & submittals (embedded per clause),
line items, procurement, shipments, schedule (dates computed by CPM), test
procedures, RFIs, and narrative docs.
"""
from __future__ import annotations

import json

from . import canonical, cpm, db, docgen, ingest


def _seed_documents(conn) -> None:
    # Specs — one citable chunk per clause.
    for section, spec in canonical.SPECS.items():
        prechunked = [
            {"text": docgen.render_spec_clause(section, c), "section_ref": f"{section} / {c['ref']}"}
            for c in spec["clauses"]
        ]
        ingest.upsert_document(
            conn,
            doc_id=f"SPEC-{section.replace(' ', '')}",
            doc_type="spec",
            title=f"{section} {spec['title']}",
            content=docgen.render_spec_document(section),
            discipline=spec["discipline"],
            revision="Rev C",
            prechunked=prechunked,
        )

    # Submittals — prose-chunked; keep spec_section in the title for filtering.
    for sub in canonical.SUBMITTALS:
        ingest.upsert_document(
            conn,
            doc_id=sub["id"],
            doc_type="submittal",
            title=f"Submittal {sub['equipment_tag']} ({sub['spec_section']}) — {sub['vendor']}",
            content=docgen.render_submittal_document(sub),
            discipline=canonical.SPECS[sub["spec_section"]]["discipline"],
            revision="Rev A",
        )

    # RFIs as documents (question + answer) for RAG breadth + citations.
    for num, q, a, disc, refs, status in canonical.RFIS:
        ingest.upsert_document(
            conn,
            doc_id=num,
            doc_type="rfi",
            title=f"{num}: {q[:60]}",
            content=f"RFI {num}\nQuestion: {q}\nAnswer: {a}\nSpec references: {', '.join(refs)}",
            discipline=disc,
        )

    # Narrative docs (minutes / change orders).
    for d in canonical.NARRATIVE_DOCS:
        ingest.upsert_document(
            conn,
            doc_id=d["id"],
            doc_type=d["type"],
            title=d["title"],
            content=d["content"],
            discipline=d.get("discipline"),
        )


def _seed_relational(conn) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO line_items (id, tag, description, discipline, spec_section, qty, unit, criticality) "
        "VALUES (?,?,?,?,?,?,?,?)",
        canonical.LINE_ITEMS,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO procurement_orders (id, line_item_id, vendor, po_date, promised_date, status, submittal_doc_id) "
        "VALUES (?,?,?,?,?,?,?)",
        canonical.PROCUREMENT,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO shipments (id, po_id, description, origin, current_lat, current_lng, eta, required_on_site, status, tier_supplier) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        canonical.SHIPMENTS,
    )
    for tp in canonical.TEST_PROCEDURES:
        conn.execute(
            "INSERT OR REPLACE INTO test_procedures (id, system, level, name, acceptance_criteria, standard_ref) "
            "VALUES (?,?,?,?,?,?)",
            (tp["id"], tp["system"], tp["level"], tp["name"],
             json.dumps(tp["acceptance_criteria"]), tp["standard_ref"]),
        )
    for num, q, a, disc, refs, status in canonical.RFIS:
        conn.execute(
            "INSERT OR REPLACE INTO rfis (id, number, question, answer, discipline, spec_refs, status, raised_at, answered_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (num, num, q, a, disc, json.dumps(refs), status, "2026-04-01", "2026-04-03"),
        )
    conn.commit()


def _seed_schedule(conn) -> None:
    tasks = [
        {"id": t[0], "wbs": t[1], "name": t[2], "duration_days": t[3],
         "predecessors": t[4], "resource": t[5]}
        for t in canonical.SCHEDULE
    ]
    result = cpm.analyze(tasks, canonical.PROJECT["start_date"])
    for t in tasks:
        r = result["tasks"][t["id"]]
        conn.execute(
            "INSERT OR REPLACE INTO schedule_tasks "
            "(id, wbs, name, duration_days, planned_start, planned_end, actual_start, actual_end, predecessors, resource, is_critical) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (t["id"], t["wbs"], t["name"], t["duration_days"],
             r["early_start"], r["early_finish"], None, None,
             json.dumps(t["predecessors"]), t["resource"], 1 if r["is_critical"] else 0),
        )
    conn.commit()
    return result


def run() -> dict:
    db.reset_db()
    conn = db.connect()
    try:
        _seed_documents(conn)
        _seed_relational(conn)
        sched = _seed_schedule(conn)
        counts = {
            "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
            "line_items": conn.execute("SELECT COUNT(*) FROM line_items").fetchone()[0],
            "schedule_tasks": conn.execute("SELECT COUNT(*) FROM schedule_tasks").fetchone()[0],
            "shipments": conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0],
            "rfis": conn.execute("SELECT COUNT(*) FROM rfis").fetchone()[0],
            "test_procedures": conn.execute("SELECT COUNT(*) FROM test_procedures").fetchone()[0],
        }
    finally:
        conn.close()
    return {"counts": counts, "project_finish": sched["project_finish"],
            "critical_path": sched["critical_path"]}


if __name__ == "__main__":
    out = run()
    print("Seed complete.")
    for k, v in out["counts"].items():
        print(f"  {k:16} {v}")
    print(f"  project_finish   {out['project_finish']}")
    print(f"  critical_path    {' -> '.join(out['critical_path'])}")
