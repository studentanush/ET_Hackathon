"""Commissioning QA Copilot (slice).

Deterministic validation of engineer readings against acceptance criteria; a
failed step auto-raises an NCR with the standard citation. Test record narrative
is generated as an as-commissioned summary.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import repository


def _cmp(reading, op, target) -> bool:
    try:
        if op == "between":
            lo, hi = target
            return float(lo) <= float(reading) <= float(hi)
        if op == "==":
            if isinstance(target, bool):
                return bool(reading) == target
            return str(reading).strip().lower() == str(target).strip().lower()
        r, t = float(reading), float(target)
        return {"<=": r <= t, ">=": r >= t, "<": r < t, ">": r > t}.get(op, False)
    except (ValueError, TypeError):
        return False


def validate(conn, procedure_id: str, readings: dict, *, executed_by: str = "Cx Engineer") -> dict:
    proc = repository.get_test_procedure(conn, procedure_id)
    if not proc:
        raise ValueError(f"Unknown procedure {procedure_id}")
    steps, all_pass = [], True
    for c in proc["acceptance_criteria"]:
        val = readings.get(c["param"])
        ok = _cmp(val, c["op"], c["target"]) if val is not None else False
        all_pass = all_pass and ok
        tgt = (f"{c['op']} {c['target']}" if c["op"] != "between"
               else f"{c['target'][0]}..{c['target'][1]}")
        steps.append({"param": c["param"], "reading": "—" if val is None else str(val),
                      "target": f"{tgt} {c['unit']}".strip(), "result": "PASS" if ok else "FAIL"})
    result = "PASS" if all_pass else "FAIL"
    now = datetime.now(timezone.utc).isoformat()
    rec_id = f"TR-{procedure_id}-{now[:10]}"

    ncr_id = None
    if not result == "PASS":
        failed = [s["param"] for s in steps if s["result"] == "FAIL"]
        ncr_id = f"NCR-CX-{procedure_id}"
        repository.create_ncr(conn, {
            "id": ncr_id, "source_module": "commissioning", "severity": "major",
            "description": f"{proc['name']} failed on: {', '.join(failed)}.",
            "spec_citation": proc["standard_ref"], "equipment_tag": proc["system"],
            "raised_at": now,
        })
    repository.save_test_record(conn, {
        "id": rec_id, "procedure_id": procedure_id, "executed_by": executed_by,
        "executed_at": now, "readings": readings, "result": result, "ncr_id": ncr_id,
    })
    return {"record_id": rec_id, "procedure": proc["name"], "standard_ref": proc["standard_ref"],
            "overall": result, "steps": steps, "ncr_id": ncr_id, "executed_by": executed_by,
            "executed_at": now}
