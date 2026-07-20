"""Spec -> Rule Compiler (isolated demo feature).

Takes a spec document's free prose and compiles it into the same structured
clause schema used by canonical.SPECS ({ref, param, op, value, unit, text,
severity}). Read-only: it returns a CompiledSpec and writes nothing — it does
not touch the DB, canonical.py, or the compliance agent's flow.
"""
from __future__ import annotations

from .. import llm
from ..schemas import CompiledSpec

SYS = (
    "You are a specifications engineer. You are given the free-text of a single "
    "specification section for a data-centre EPC project. Compile it into machine-"
    "checkable clauses.\n"
    "- Extract EACH distinct, testable requirement as one clause.\n"
    "- param: a short snake_case key (e.g. 'flow_rate_lpm', 'detection_type', "
    "'redundancy_required').\n"
    "- op: '>=' or '<=' for numeric minimums/maximums, '==' for an exact required "
    "value/type, 'bool' for a mandatory yes/no requirement, 'between' for a range.\n"
    "- value: the threshold as a string (for 'between', 'lo..hi'; for 'bool', 'true').\n"
    "- unit: the unit if any, else empty.\n"
    "- text: restate the requirement in one concise sentence.\n"
    "- severity: 'major' by default; 'critical' only for safety/life-safety or "
    "fault-rating items; 'minor' for documentation/cosmetic items.\n"
    "- ref: use the clause number if present, otherwise assign sequential numbers "
    "like 2.1, 2.2, ...\n"
    "Infer a sensible section code and title from the text. Do not invent "
    "requirements that are not stated."
)


def compile_spec(raw_text: str, *, effort: str = "high") -> CompiledSpec:
    """Compile raw spec prose into a CompiledSpec. Returns the object; no writes."""
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text is empty")
    return llm.complete_json(
        [
            {"role": "system", "content": SYS},
            {"role": "user", "content": f"SPECIFICATION TEXT:\n\n{raw_text.strip()}"},
        ],
        CompiledSpec,
        effort=effort,
        temperature=0.1,
        max_tokens=3000,
    )
