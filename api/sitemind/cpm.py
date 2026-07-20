"""Critical Path Method engine (deterministic, no LLM).

Forward/backward pass over a finish-to-start task network -> early/late dates,
total float, the critical path, and project finish. `what_if` re-runs the pass
with an injected delay so mitigations can be *verified* by math, not guessed by
the model (plan §6.2: "agent proposes, math disposes").

Durations and offsets are in calendar days for demo simplicity.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any

import networkx as nx


def _parse(d: str | date) -> date:
    if isinstance(d, date):
        return d
    return datetime.fromisoformat(str(d)[:10]).date()


def _build_graph(tasks: list[dict]) -> nx.DiGraph:
    g = nx.DiGraph()
    ids = {t["id"] for t in tasks}
    for t in tasks:
        g.add_node(t["id"], duration=int(t.get("duration_days", 0) or 0), name=t.get("name", t["id"]))
    for t in tasks:
        for p in t.get("predecessors", []) or []:
            if p in ids:
                g.add_edge(p, t["id"])
    if not nx.is_directed_acyclic_graph(g):
        cycle = nx.find_cycle(g)
        raise ValueError(f"Schedule has a dependency cycle: {cycle}")
    return g


def analyze(tasks: list[dict], project_start: str | date) -> dict[str, Any]:
    """Return per-task CPM results plus project-level summary.

    Each task result: early_start, early_finish, late_start, late_finish (ISO
    dates), total_float (days), is_critical (bool).
    """
    start = _parse(project_start)
    g = _build_graph(tasks)
    order = list(nx.topological_sort(g))
    dur = {n: g.nodes[n]["duration"] for n in g.nodes}

    # Forward pass: earliest start/finish as day-offsets from project_start.
    es: dict[str, int] = {}
    ef: dict[str, int] = {}
    for n in order:
        preds = list(g.predecessors(n))
        es[n] = max((ef[p] for p in preds), default=0)
        ef[n] = es[n] + dur[n]

    project_len = max(ef.values(), default=0)

    # Backward pass: latest finish/start.
    lf: dict[str, int] = {}
    ls: dict[str, int] = {}
    for n in reversed(order):
        succs = list(g.successors(n))
        lf[n] = min((ls[s] for s in succs), default=project_len)
        ls[n] = lf[n] - dur[n]

    results = {}
    critical = []
    for n in g.nodes:
        total_float = ls[n] - es[n]
        is_crit = total_float == 0
        if is_crit:
            critical.append(n)
        results[n] = {
            "id": n,
            "name": g.nodes[n]["name"],
            "duration_days": dur[n],
            "early_start": (start + timedelta(days=es[n])).isoformat(),
            "early_finish": (start + timedelta(days=ef[n])).isoformat(),
            "late_start": (start + timedelta(days=ls[n])).isoformat(),
            "late_finish": (start + timedelta(days=lf[n])).isoformat(),
            "total_float": total_float,
            "is_critical": is_crit,
        }

    # Order the critical path by early start for readability.
    critical_path = sorted(critical, key=lambda n: es[n])
    finish_date = (start + timedelta(days=project_len)).isoformat()
    return {
        "project_start": start.isoformat(),
        "project_finish": finish_date,
        "duration_days": project_len,
        "critical_path": critical_path,
        "tasks": results,
    }


def what_if(
    tasks: list[dict],
    project_start: str | date,
    *,
    delay_task_id: str,
    delay_days: int,
) -> dict[str, Any]:
    """Inject `delay_days` extra duration into one task; report finish impact.

    Returns baseline finish, new finish, and slip in days. If the delayed task
    has float >= delay_days, the project finish does not move (slip == 0).
    """
    baseline = analyze(tasks, project_start)
    mutated = []
    found = False
    for t in tasks:
        t2 = dict(t)
        if t2["id"] == delay_task_id:
            t2["duration_days"] = int(t2.get("duration_days", 0) or 0) + int(delay_days)
            found = True
        mutated.append(t2)
    if not found:
        raise ValueError(f"Unknown task id: {delay_task_id}")
    delayed = analyze(mutated, project_start)
    slip = delayed["duration_days"] - baseline["duration_days"]
    return {
        "delay_task_id": delay_task_id,
        "delay_days": delay_days,
        "baseline_finish": baseline["project_finish"],
        "new_finish": delayed["project_finish"],
        "project_slip_days": slip,
        "absorbed_by_float": slip < delay_days,
        "new_critical_path": delayed["critical_path"],
    }


def monte_carlo(
    tasks: list[dict],
    project_start: str | date,
    *,
    iterations: int = 500,
    spread_pct: float = 0.15,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Probabilistic finish-date distribution (additive; wraps analyze()).

    Each iteration perturbs every task's duration by a triangular distribution
    centred on its planned duration (+/- spread_pct, min 1 day), then runs the
    EXISTING analyze() unchanged. Returns P10/P50/P90 finish dates plus a weekly
    histogram. This does not alter analyze()/what_if() — it only calls analyze().
    """
    rng = random.Random(seed)
    start = _parse(project_start)
    baseline = analyze(tasks, start)
    finish_offsets: list[int] = []

    for _ in range(iterations):
        sampled = []
        for t in tasks:
            d = int(t.get("duration_days", 0) or 0)
            if d <= 0:
                sampled.append(dict(t))
                continue
            lo = max(1, d * (1 - spread_pct))
            hi = d * (1 + spread_pct)
            dur = max(1, round(rng.triangular(lo, hi, d)))
            sampled.append({**t, "duration_days": dur})
        res = analyze(sampled, start)
        finish_offsets.append(res["duration_days"])

    finish_offsets.sort()

    def pct(p: float) -> int:
        idx = min(len(finish_offsets) - 1, int(p * (len(finish_offsets) - 1)))
        return finish_offsets[idx]

    def as_date(days: int) -> str:
        return (start + timedelta(days=days)).isoformat()

    # weekly histogram buckets
    lo, hi = finish_offsets[0], finish_offsets[-1]
    bucket = 7
    counts: dict[int, int] = {}
    for o in finish_offsets:
        b = (o // bucket) * bucket
        counts[b] = counts.get(b, 0) + 1
    histogram = [
        {"finish": as_date(b), "days": b, "count": counts.get(b, 0)}
        for b in range(lo - lo % bucket, hi + bucket, bucket)
    ]

    return {
        "iterations": iterations,
        "spread_pct": spread_pct,
        "deterministic_finish": baseline["project_finish"],
        "p10_finish": as_date(pct(0.10)),
        "p50_finish": as_date(pct(0.50)),
        "p90_finish": as_date(pct(0.90)),
        "p10_days": pct(0.10),
        "p50_days": pct(0.50),
        "p90_days": pct(0.90),
        "histogram": histogram,
    }
