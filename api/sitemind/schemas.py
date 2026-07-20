"""Pydantic models for structured LLM outputs and API responses."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- compliance ------------------------------------------------------------
class Citation(BaseModel):
    doc_id: str = ""
    section_ref: str = ""


class Finding(BaseModel):
    clause_ref: str = Field(description="Spec clause, e.g. '2.3.1'")
    requirement: str = Field(description="What the spec requires")
    submittal_value: str = Field(description="What the submittal states")
    verdict: Literal["COMPLIANT", "DEVIATION", "UNCLEAR"]
    severity: Literal["minor", "major", "critical", "none"] = "none"
    citation: Citation = Citation()
    recommended_action: str = ""


class ComplianceReport(BaseModel):
    equipment_tag: str
    spec_section: str
    findings: list[Finding]
    summary_verdict: Literal["COMPLIANT", "NON_COMPLIANT"]
    review_time_saved_hours: float = 5.5


# --- schedule risk ---------------------------------------------------------
class Mitigation(BaseModel):
    option: str = Field(description="Concrete action, e.g. 'air-freight switchgear'")
    schedule_recovery_days: int = Field(description="Days recovered (agent estimate; verified by CPM)")
    cost_impact: str = Field(description="Qualitative or ballpark cost")
    tradeoff: str = ""


class RiskItem(BaseModel):
    title: str
    risk_type: str
    description: str
    probability: float = Field(ge=0, le=1)
    impact_days: int
    affected_tasks: list[str] = []
    mitigations: list[Mitigation] = []


class RiskRegister(BaseModel):
    risks: list[RiskItem]


# --- commissioning ---------------------------------------------------------
class StepResult(BaseModel):
    param: str
    reading: str
    target: str
    result: Literal["PASS", "FAIL"]


class TestValidation(BaseModel):
    procedure_id: str
    overall: Literal["PASS", "FAIL"]
    steps: list[StepResult]
    note: str = ""


# --- spec -> rule compiler -------------------------------------------------
class CompiledClause(BaseModel):
    ref: str = Field(description="Clause number, e.g. '2.3.1' (infer if absent)")
    param: str = Field(description="snake_case machine key for the requirement")
    op: Literal[">=", "<=", "==", "bool", "between"]
    value: str = Field(description="Threshold as a string; UI displays as-is")
    unit: str = ""
    text: str = Field(description="The requirement restated concisely")
    severity: Literal["minor", "major", "critical"]


class CompiledSpec(BaseModel):
    section: str
    title: str
    clauses: list[CompiledClause]
