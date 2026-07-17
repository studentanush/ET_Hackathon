"""Render canonical facts into realistic document prose.

Deterministic templating (no API calls) so spec clauses and submittal datasheets
are always internally consistent with canonical.py. Each spec clause becomes its
own chunk so citations can point at a specific clause ref.
"""
from __future__ import annotations

from . import canonical


def _fmt_value(v) -> str:
    if isinstance(v, bool):
        return "Required / Provided" if v else "Not provided"
    return str(v)


def render_spec_clause(section: str, clause: dict) -> str:
    """One clause -> one chunk of spec text."""
    spec = canonical.SPECS[section]
    head = f"SPEC {section} {spec['title']} — Clause {clause['ref']}"
    body = clause["text"]
    ref = f"(Standards: {spec['standard_ref']})"
    return f"{head}\n{body} {ref}"


def render_spec_document(section: str) -> str:
    spec = canonical.SPECS[section]
    lines = [
        f"SPECIFICATION SECTION {section} — {spec['title'].upper()}",
        f"Discipline: {spec['discipline']}   Applicable standards: {spec['standard_ref']}",
        f"Project: {canonical.PROJECT['name']} ({canonical.PROJECT['location']})",
        "",
        "PART 2 — PRODUCTS / PART 3 — EXECUTION",
    ]
    for c in spec["clauses"]:
        lines.append(f"\n{c['ref']}  {c['text']}")
    return "\n".join(lines)


def render_submittal_document(sub: dict) -> str:
    """Vendor submittal / technical datasheet with a compliance statement table."""
    spec = canonical.SPECS[sub["spec_section"]]
    lines = [
        f"VENDOR SUBMITTAL {sub['id']} — {sub['equipment_tag']}",
        f"Equipment: {spec['title']}   Spec section: {sub['spec_section']}",
        f"Vendor: {sub['vendor']}   Model: {sub['model']}",
        f"Project: {canonical.PROJECT['name']}",
        "",
        "TECHNICAL DATA / COMPLIANCE STATEMENT",
    ]
    # Emit one line per spec clause with the submitted value, so a reader (and
    # the compliance agent) can compare requirement vs submitted value.
    for c in spec["clauses"]:
        val = sub["values"].get(c["param"], "not stated")
        lines.append(
            f"- Clause {c['ref']} [{c['param']}]: requirement \"{c['text']}\" | "
            f"submitted value: {_fmt_value(val)}"
        )
    return "\n".join(lines)
