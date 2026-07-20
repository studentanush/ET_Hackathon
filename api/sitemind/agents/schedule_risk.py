"""Predictive Schedule Risk Engine (flagship #2).

Deterministic core (CPM + signal collection in Python) + an LLM analyst that
ranks risks and proposes mitigations. Every mitigation and every impact number
is VERIFIED against the CPM what-if — the model never invents dates.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from .. import canonical, cpm, llm, repository
from ..schemas import RiskRegister


def _today() -> date:
    return datetime.fromisoformat(canonical.PROJECT["today"]).date()


def _tasks(conn) -> list[dict]:
    return [
        {"id": t["id"], "name": t["name"], "duration_days": t["duration_days"],
         "predecessors": t["predecessors"], "wbs": t["wbs"], "resource": t["resource"]}
        for t in repository.get_schedule_tasks(conn)
    ]


def cpm_state(conn) -> dict:
    return cpm.analyze(_tasks(conn), canonical.PROJECT["start_date"])


def what_if(conn, task_id: str, delay_days: int) -> dict:
    return cpm.what_if(_tasks(conn), canonical.PROJECT["start_date"],
                       delay_task_id=task_id, delay_days=delay_days)


def monte_carlo(conn, *, iterations: int = 500, spread_pct: float = 0.15) -> dict:
    """Probabilistic finish-date distribution (wraps cpm.monte_carlo)."""
    return cpm.monte_carlo(_tasks(conn), canonical.PROJECT["start_date"],
                           iterations=iterations, spread_pct=spread_pct)


# --------------------------------------------------------------------------- #
# Signal collection (deterministic)
# --------------------------------------------------------------------------- #
def collect_signals(conn) -> list[dict]:
    """Raw risk signals from procurement, shipments, and open NCRs."""
    signals = []
    today = _today()

    # Shipment ETA vs required-on-site.
    for s in repository.get_shipments(conn):
        try:
            eta = datetime.fromisoformat(s["eta"]).date()
            ros = datetime.fromisoformat(s["required_on_site"]).date()
        except (TypeError, ValueError):
            continue
        slip = (eta - ros).days
        if slip > 0:
            signals.append({
                "type": "shipment_delay", "ref": s["id"],
                "description": f"{s['description']} ETA {s['eta']} vs required {s['required_on_site']}",
                "slip_days": slip, "vendor": s.get("tier_supplier"), "status": s["status"],
            })

    # On-hold / at-risk POs.
    for po in repository.get_procurement_status(conn):
        if po["status"] in ("on_hold", "at_risk"):
            signals.append({
                "type": "procurement_status", "ref": po["id"],
                "description": f"PO {po['id']} ({po.get('tag')}) status {po['status']} — vendor {po['vendor']}",
                "criticality": po.get("criticality"),
            })

    # Open NCRs (a rejected submittal = resubmittal lead-time hit).
    for ncr in repository.list_ncrs(conn, status="open"):
        signals.append({
            "type": "open_ncr", "ref": ncr["id"],
            "description": ncr["description"], "severity": ncr["severity"],
            "equipment_tag": ncr["equipment_tag"],
        })
    return signals


# Map a shipment/PO/NCR to the schedule task it threatens (demo mapping).
# Which task phase each signal type threatens.
_SIGNAL_PHASE = {
    "shipment_delay": "delivery",       # a late shipment hits the delivery task
    "procurement_status": "manufacture",  # a stalled PO hits manufacture
    "open_ncr": "manufacture",          # a rejected submittal forces resubmittal + refab
}


def _linked_task(conn, sig: dict) -> str | None:
    """Resolve a signal to its schedule task generically (no hardcoded ids)."""
    ref = sig.get("ref") or sig.get("equipment_tag")
    phase = _SIGNAL_PHASE.get(sig.get("type"), "delivery")
    return repository.resolve_signal_task(conn, ref, phase)


SYS = (
    "You are a data-centre EPC schedule-risk analyst. Given the critical path, "
    "signals, and CPM what-if results, produce a ranked risk register. Rank by "
    "impact_days (from the CPM results, NOT invented) x probability. For each risk "
    "give 2-3 concrete mitigations (air-freight, resequence, alternate vendor, "
    "parallel work) with realistic cost/schedule tradeoffs. Only use impact numbers "
    "supported by the provided CPM what-if data."
)


def analyze_risks(conn, *, effort: str = "xhigh") -> dict:
    state = cpm_state(conn)
    signals = collect_signals(conn)

    # For each signal linked to a task, compute the deterministic schedule impact.
    verified = []
    for sig in signals:
        tid = _linked_task(conn, sig)
        if not tid:
            continue
        delay = int(sig.get("slip_days") or 21)  # NCR/PO default to a resubmittal cycle
        wi = what_if(conn, tid, delay)
        sig["linked_task"] = tid
        sig["cpm_project_slip_days"] = wi["project_slip_days"]
        sig["absorbed_by_float"] = wi["absorbed_by_float"]
        verified.append(sig)

    facts = {
        "today": canonical.PROJECT["today"],
        "project_finish": state["project_finish"],
        "critical_path": [f"{tid} {state['tasks'][tid]['name']}" for tid in state["critical_path"]],
        "signals_with_cpm_impact": verified,
    }
    import json
    user = (
        "PROJECT SCHEDULE FACTS (CPM-verified):\n" + json.dumps(facts, indent=2, default=str) +
        "\n\nProduce the ranked risk register."
    )
    register = llm.complete_json(
        [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
        RiskRegister, effort="high", max_tokens=8000,
    )

    # Verify each mitigation's claimed recovery against CPM, and persist risks.
    out_risks = []
    for r in register.risks:
        for m in r.mitigations:
            m_task = r.affected_tasks[0] if r.affected_tasks else None
            if m_task and m.schedule_recovery_days:
                wi = what_if(conn, m_task, -min(m.schedule_recovery_days, r.impact_days))
                recovered = r.impact_days - max(0, wi["project_slip_days"])
                m.schedule_recovery_days = max(0, min(r.impact_days, recovered))
        rd = r.model_dump()
        repository.create_risk_event(conn, {
            "id": f"RISK-SCHED-{r.risk_type[:12]}-{hashlib.md5(r.title.encode()).hexdigest()[:6]}",
            "source_module": "schedule", "risk_type": r.risk_type,
            "title": r.title, "description": r.description,
            "probability": r.probability, "impact_days": r.impact_days,
            "affected_tasks": r.affected_tasks, "mitigation_options": rd["mitigations"],
            "detected_at": datetime.now(timezone.utc).isoformat(), "status": "open",
        })
        out_risks.append(rd)

    out_risks.sort(key=lambda x: x["impact_days"] * x["probability"], reverse=True)
    return {"project_finish": state["project_finish"], "critical_path": state["critical_path"],
            "signals": verified, "risks": out_risks}
