"""Cross-module intelligence — the 'one intelligence graph' layer.

Three deterministic wirings on top of the shared risk_events table:
  1. supply -> schedule       (sync_supply_risks)
  2. schedule -> commissioning (commissioning_readiness)
  3. simulation clock         (build_simulation) — when a risk was DETECTED vs
     when it BITES, so we can show the early-warning lead time.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import networkx as nx

from . import canonical, repository
from .agents import schedule_risk


def _d(s: str) -> date:
    return datetime.fromisoformat(str(s)[:10]).date()


def _today() -> date:
    return _d(canonical.PROJECT["today"])


# --------------------------------------------------------------------------- #
# 1. supply -> schedule : at-risk shipments create/update schedule risk_events
# --------------------------------------------------------------------------- #
def sync_supply_risks(conn) -> list[dict]:
    """Every at-risk shipment (ETA later than required-on-site) becomes a schedule
    risk_event, with its project impact computed by the CPM what-if."""
    raised = []
    for s in repository.get_shipments(conn):
        try:
            slip = (_d(s["eta"]) - _d(s["required_on_site"])).days
        except (TypeError, ValueError):
            continue
        if slip <= 0:
            continue
        task = schedule_risk._SIGNAL_TASK.get(s["id"])
        impact = slip
        if task:
            wi = schedule_risk.what_if(conn, task, slip)
            impact = wi["project_slip_days"]
        ev = repository.create_risk_event(conn, {
            "id": f"RISK-SUPPLY-{s['id']}",
            "source_module": "supply",
            "risk_type": "shipment_delay",
            "title": f"{s['description']} delivery slip ({slip}d late)",
            "description": (
                f"{s['description']} ETA {s['eta']} vs required {s['required_on_site']} "
                f"({slip} days late). CPM project impact: {impact} days."),
            "probability": 0.9 if s["status"] == "delayed" else 0.6,
            "impact_days": impact,
            "affected_tasks": [task] if task else [],
            "detected_at": canonical.SIM_DETECTION.get(s["id"], {}).get("detected_on",
                            canonical.PROJECT["today"]),
            "status": "open",
        })
        raised.append(ev)
    return raised


# --------------------------------------------------------------------------- #
# 2. schedule -> commissioning : is each test blocked by an upstream risk?
# --------------------------------------------------------------------------- #
def _schedule_graph(conn) -> nx.DiGraph:
    g = nx.DiGraph()
    for t in repository.get_schedule_tasks(conn):
        g.add_node(t["id"], name=t["name"])
        for p in t["predecessors"]:
            g.add_edge(p, t["id"])
    return g


def commissioning_readiness(conn) -> list[dict]:
    """For each commissioning test, report whether an open risk on an upstream
    schedule task blocks it (e.g. IST blocked because switchgear energization slips)."""
    g = _schedule_graph(conn)
    risks = [r for r in repository.list_risk_events(conn) if r["status"] == "open"]
    # task_id -> list of risks touching it
    risk_by_task: dict[str, list[dict]] = {}
    for r in risks:
        for t in (r["affected_tasks"] or []):
            risk_by_task.setdefault(t, []).append(r)

    out = []
    for proc in repository.list_test_procedures(conn):
        task = canonical.TEST_PROC_TASK.get(proc["id"])
        blockers = []
        if task and task in g:
            upstream = nx.ancestors(g, task) | {task}
            for tid in upstream:
                for r in risk_by_task.get(tid, []):
                    blockers.append({"risk_id": r["id"], "via_task": tid,
                                     "title": r["title"], "impact_days": r["impact_days"]})
        # de-dup by risk id, keep worst impact
        seen = {}
        for b in blockers:
            if b["risk_id"] not in seen or b["impact_days"] > seen[b["risk_id"]]["impact_days"]:
                seen[b["risk_id"]] = b
        blockers = sorted(seen.values(), key=lambda x: x["impact_days"], reverse=True)
        out.append({
            "procedure_id": proc["id"], "level": proc["level"], "name": proc["name"],
            "depends_on_task": task,
            "status": "BLOCKED" if blockers else "READY",
            "blockers": blockers,
        })
    # blocked first, then by level
    out.sort(key=lambda x: (x["status"] != "BLOCKED", x["level"]))
    return out


# --------------------------------------------------------------------------- #
# 3. simulation clock : detection vs impact timeline
# --------------------------------------------------------------------------- #
def build_simulation(conn) -> dict:
    """Timeline of weekly buckets plus, per risk signal, the date it was DETECTED
    and the date it BITES (required-on-site / dependent critical date). The UI
    scrubs a date and shows the early-warning lead time."""
    state = schedule_risk.cpm_state(conn)
    start = _d(state["project_start"])
    finish = _d(state["project_finish"])

    # weekly buckets (Mondays) covering start..finish (+2 weeks headroom)
    weeks = []
    w = start - timedelta(days=start.weekday())
    end = finish + timedelta(days=14)
    while w <= end:
        weeks.append(w.isoformat())
        w += timedelta(days=7)

    shipments = {s["id"]: s for s in repository.get_shipments(conn)}
    events = []
    for ref, meta in canonical.SIM_DETECTION.items():
        detected = _d(meta["detected_on"])
        bites = None
        impact_days = None
        task = schedule_risk._SIGNAL_TASK.get(ref)

        if ref in shipments:
            bites = _d(shipments[ref]["required_on_site"])
        elif task:
            # bites when the linked (critical) task was planned to start
            tinfo = state["tasks"].get(task)
            if tinfo:
                bites = _d(tinfo["early_start"])
        if bites is None:
            bites = detected + timedelta(days=30)

        if task:
            slip = (_d(shipments[ref]["eta"]) - _d(shipments[ref]["required_on_site"])).days if ref in shipments else 21
            impact_days = schedule_risk.what_if(conn, task, max(slip, 1))["project_slip_days"]
        elif meta["source"] == "compliance":
            # Rejection forces a resubmittal + refab cycle on the critical path.
            impact_days = 21

        lead_days = (bites - detected).days
        if lead_days < 0:
            continue  # not a forward-looking early warning; skip
        events.append({
            "ref": ref, "title": meta["title"], "source": meta["source"],
            "detected_on": detected.isoformat(), "bites_on": bites.isoformat(),
            "lead_days": lead_days, "lead_weeks": round(lead_days / 7, 1),
            "impact_days": impact_days, "affected_task": task,
        })

    events.sort(key=lambda e: e["detected_on"])
    # Headline = the earliest-warning risk that carries real schedule impact.
    headline = max((e for e in events if e["impact_days"]),
                   key=lambda e: e["lead_days"], default=None)
    return {
        "project_start": start.isoformat(),
        "project_finish": finish.isoformat(),
        "today": canonical.PROJECT["today"],
        "weeks": weeks,
        "events": events,
        "headline": headline,
    }
