"""Canonical facts for Project Meghdoot — the single source of truth.

Plan §10 names internal inconsistency as the #1 risk. Everything the seed script
loads (specs, submittals, line items, schedule, procurement, RFIs, tests) is
derived from THIS file, so tags / spec sections / dates / vendors cross-reference
correctly by construction.

The seeded submittal deviations here are the LABELLED GROUND TRUTH for the
compliance-accuracy evaluation (plan §2, §6.1). Each `deviations` entry is a real
non-conformance the compliance agent should catch; everything else is compliant.
"""
from __future__ import annotations

PROJECT = {
    "name": "Project Meghdoot",
    "description": "24 MW hyperscale data centre campus — Phase 1: one 8 MW data hall",
    "location": "Navi Mumbai, Maharashtra, India",
    "client": "Meghdoot Hyperscale DC Pvt. Ltd.",
    "epc_contractor": "Larsen Infra EPC",
    "tier": "Uptime Tier III",
    "start_date": "2026-01-05",
    "today": "2026-07-17",  # matches the demo 'current date'
}

# --------------------------------------------------------------------------- #
# Specifications (CSI MasterFormat). Clauses carry a machine-checkable
# requirement so we can both render realistic spec prose AND label deviations.
#   op: ">=" | "<=" | "==" | "bool"  (bool => value True is required)
# --------------------------------------------------------------------------- #
SPECS = {
    "26 33 53": {
        "title": "Static Uninterruptible Power Supply (UPS)",
        "discipline": "Electrical",
        "standard_ref": "IEC 62040-3, IEEE 519, TIA-942",
        "clauses": [
            {"ref": "2.1.1", "param": "topology", "op": "==", "value": "double-conversion online", "unit": "", "text": "UPS shall be true double-conversion (online) with no break on mains failure.", "severity": "major"},
            {"ref": "2.2.1", "param": "module_kw", "op": ">=", "value": 500, "unit": "kW", "text": "Each UPS module shall be rated not less than 500 kW at 0.9 pf.", "severity": "major"},
            {"ref": "2.3.1", "param": "input_voltage_tolerance_pct", "op": ">=", "value": 15, "unit": "%", "text": "Input voltage operating window shall be at least +/-15% of nominal without battery discharge.", "severity": "major"},
            {"ref": "2.3.2", "param": "output_thd_pct", "op": "<=", "value": 3, "unit": "%", "text": "Output voltage THD shall not exceed 3% on linear load.", "severity": "minor"},
            {"ref": "2.4.1", "param": "efficiency_pct", "op": ">=", "value": 96, "unit": "%", "text": "Double-conversion efficiency at full load shall be not less than 96%.", "severity": "major"},
            {"ref": "2.5.1", "param": "battery_autonomy_min", "op": ">=", "value": 5, "unit": "min", "text": "Battery autonomy at full rated load shall be not less than 5 minutes.", "severity": "major"},
            {"ref": "2.6.1", "param": "seismic_cert", "op": "bool", "value": True, "unit": "", "text": "Unit shall carry seismic qualification certification per IBC / IEEE 693.", "severity": "major"},
            {"ref": "3.1.1", "param": "factory_witness_test", "op": "bool", "value": True, "unit": "", "text": "Factory witness test (FWT) with client attendance is mandatory prior to shipment.", "severity": "minor"},
        ],
    },
    "26 32 13": {
        "title": "Diesel Engine Generator Sets",
        "discipline": "Electrical",
        "standard_ref": "ISO 8528, CPCB IV+, IEC 60034",
        "clauses": [
            {"ref": "2.1.1", "param": "prime_power_kwe", "op": ">=", "value": 2500, "unit": "kWe", "text": "Each set shall deliver not less than 2500 kWe prime power at site conditions.", "severity": "major"},
            {"ref": "2.2.1", "param": "fuel_autonomy_hr", "op": ">=", "value": 8, "unit": "hr", "text": "Belly/day tank shall provide not less than 8 hours autonomy at prime load.", "severity": "major"},
            {"ref": "2.3.1", "param": "emissions", "op": "==", "value": "CPCB IV+", "unit": "", "text": "Engine shall comply with CPCB IV+ emission norms.", "severity": "major"},
            {"ref": "2.4.1", "param": "single_step_load_pct", "op": ">=", "value": 100, "unit": "%", "text": "Set shall accept 100% block load in a single step per ISO 8528-5 class G3.", "severity": "major"},
            {"ref": "2.5.1", "param": "sound_dba_at_1m", "op": "<=", "value": 85, "unit": "dBA", "text": "Enclosure sound level shall not exceed 85 dBA at 1 m.", "severity": "minor"},
            {"ref": "2.6.1", "param": "governor", "op": "==", "value": "electronic isochronous", "unit": "", "text": "Governing shall be electronic isochronous.", "severity": "minor"},
        ],
    },
    "26 13 13": {
        "title": "Medium-Voltage Metal-Clad Switchgear",
        "discipline": "Electrical",
        "standard_ref": "IEC 62271-200",
        "clauses": [
            {"ref": "2.1.1", "param": "rated_voltage_kv", "op": "==", "value": 11, "unit": "kV", "text": "Rated voltage shall be 11 kV, 50 Hz, three phase.", "severity": "major"},
            {"ref": "2.2.1", "param": "short_circuit_ka", "op": ">=", "value": 25, "unit": "kA", "text": "Short-circuit withstand shall be not less than 25 kA for 3 seconds.", "severity": "major"},
            {"ref": "2.3.1", "param": "busbar_rating_a", "op": ">=", "value": 2500, "unit": "A", "text": "Main busbar continuous rating shall be not less than 2500 A.", "severity": "major"},
            {"ref": "2.4.1", "param": "arc_containment", "op": "bool", "value": True, "unit": "", "text": "Internal arc classification IAC AFLR per IEC 62271-200 is required.", "severity": "major"},
            {"ref": "2.5.1", "param": "ip_rating", "op": ">=", "value": 4, "unit": "IP4X", "text": "Enclosure protection shall be not less than IP4X.", "severity": "minor"},
            {"ref": "3.1.1", "param": "type_test_cert", "op": "bool", "value": True, "unit": "", "text": "Complete type test certificates from an accredited lab are mandatory.", "severity": "major"},
        ],
    },
    "23 81 00": {
        "title": "Computer Room Air Handlers (CRAH)",
        "discipline": "Mechanical",
        "standard_ref": "ASHRAE TC9.9, TIA-942",
        "clauses": [
            {"ref": "2.1.1", "param": "sensible_kw", "op": ">=", "value": 120, "unit": "kW", "text": "Net sensible cooling capacity shall be not less than 120 kW per unit.", "severity": "major"},
            {"ref": "2.2.1", "param": "airflow_m3h", "op": ">=", "value": 30000, "unit": "m3/h", "text": "Rated airflow shall be not less than 30,000 m3/h.", "severity": "major"},
            {"ref": "2.3.1", "param": "ec_fans", "op": "bool", "value": True, "unit": "", "text": "Fans shall be EC (electronically commutated) plug-fan type.", "severity": "minor"},
            {"ref": "2.4.1", "param": "supply_temp_control_c", "op": "<=", "value": 1, "unit": "C", "text": "Supply air temperature control shall be within +/-1 C of setpoint.", "severity": "minor"},
            {"ref": "2.5.1", "param": "redundancy_n_plus_1", "op": "bool", "value": True, "unit": "", "text": "CRAH deployment shall be N+1 redundant per data hall.", "severity": "major"},
        ],
    },
    "26 25 00": {
        "title": "Enclosed Bus Assemblies (Busway)",
        "discipline": "Electrical",
        "standard_ref": "IEC 61439-6",
        "clauses": [
            {"ref": "2.1.1", "param": "current_rating_a", "op": ">=", "value": 4000, "unit": "A", "text": "Busway continuous current rating shall be not less than 4000 A.", "severity": "major"},
            {"ref": "2.2.1", "param": "short_circuit_ka", "op": ">=", "value": 100, "unit": "kA", "text": "Short-circuit withstand shall be not less than 100 kA.", "severity": "major"},
            {"ref": "2.3.1", "param": "ip_rating", "op": ">=", "value": 55, "unit": "IP", "text": "Outdoor busway runs shall be not less than IP55.", "severity": "major"},
            {"ref": "2.4.1", "param": "tap_off_provision", "op": "bool", "value": True, "unit": "", "text": "Plug-in tap-off provisions at maximum 1.5 m centres are required.", "severity": "minor"},
        ],
    },
}

# --------------------------------------------------------------------------- #
# Submittals with real submitted values. `deviations` = labelled ground truth.
# A submittal is COMPLIANT unless a param appears in `deviations`.
# --------------------------------------------------------------------------- #
SUBMITTALS = [
    {
        "id": "SUB-UPS-A", "equipment_tag": "UPS-A-01", "spec_section": "26 33 53",
        "vendor": "PowerCore Systems", "model": "PC-Guardian 600",
        "values": {"topology": "double-conversion online", "module_kw": 600, "input_voltage_tolerance_pct": 20,
                   "output_thd_pct": 2.5, "efficiency_pct": 96.5, "battery_autonomy_min": 7,
                   "seismic_cert": True, "factory_witness_test": True},
        "deviations": [],
    },
    {
        "id": "SUB-UPS-B", "equipment_tag": "UPS-B-01", "spec_section": "26 33 53",
        "vendor": "ELGI Power", "model": "EP-DC 550",
        "values": {"topology": "double-conversion online", "module_kw": 550, "input_voltage_tolerance_pct": 10,
                   "output_thd_pct": 2.8, "efficiency_pct": 95.0, "battery_autonomy_min": 5,
                   "seismic_cert": False, "factory_witness_test": True},
        "deviations": [
            {"clause_ref": "2.3.1", "param": "input_voltage_tolerance_pct", "submitted": "+/-10%", "expected": "+/-15%", "severity": "major", "reason": "Input window narrower than specified; will discharge battery on grid sag."},
            {"clause_ref": "2.4.1", "param": "efficiency_pct", "submitted": "95.0%", "expected": ">=96%", "severity": "major", "reason": "Efficiency below spec minimum; higher OPEX and heat load."},
            {"clause_ref": "2.6.1", "param": "seismic_cert", "submitted": "not provided", "expected": "required", "severity": "major", "reason": "No seismic qualification certificate submitted."},
        ],
    },
    {
        "id": "SUB-DG-01", "equipment_tag": "DG-01", "spec_section": "26 32 13",
        "vendor": "Kirloskar Green", "model": "KG-3000DC",
        "values": {"prime_power_kwe": 2700, "fuel_autonomy_hr": 10, "emissions": "CPCB IV+",
                   "single_step_load_pct": 100, "sound_dba_at_1m": 82, "governor": "electronic isochronous"},
        "deviations": [],
    },
    {
        "id": "SUB-DG-02", "equipment_tag": "DG-02", "spec_section": "26 32 13",
        "vendor": "Mahindra Powerol", "model": "MP-2500SG",
        "values": {"prime_power_kwe": 2500, "fuel_autonomy_hr": 6, "emissions": "CPCB IV+",
                   "single_step_load_pct": 100, "sound_dba_at_1m": 90, "governor": "electronic isochronous"},
        "deviations": [
            {"clause_ref": "2.2.1", "param": "fuel_autonomy_hr", "submitted": "6 hr", "expected": ">=8 hr", "severity": "major", "reason": "Day-tank autonomy short of spec; refuelling risk during extended outage."},
            {"clause_ref": "2.5.1", "param": "sound_dba_at_1m", "submitted": "90 dBA", "expected": "<=85 dBA", "severity": "minor", "reason": "Enclosure noise exceeds limit; extra attenuation required."},
        ],
    },
    {
        "id": "SUB-SWGR-01", "equipment_tag": "SWGR-MV-01", "spec_section": "26 13 13",
        "vendor": "Schneider Electric", "model": "SM6-24 MV",
        "values": {"rated_voltage_kv": 11, "short_circuit_ka": 21, "busbar_rating_a": 2500,
                   "arc_containment": True, "ip_rating": 4, "type_test_cert": True},
        "deviations": [
            {"clause_ref": "2.2.1", "param": "short_circuit_ka", "submitted": "21 kA", "expected": ">=25 kA", "severity": "critical", "reason": "Short-circuit withstand below spec at a CRITICAL-PATH item; safety and coordination risk. Rejection forces resubmittal + refab lead time."},
        ],
    },
    {
        "id": "SUB-CRAH-01", "equipment_tag": "CRAH-01", "spec_section": "23 81 00",
        "vendor": "STULZ India", "model": "CyberAir 3PRO",
        "values": {"sensible_kw": 130, "airflow_m3h": 32000, "ec_fans": True,
                   "supply_temp_control_c": 0.8, "redundancy_n_plus_1": True},
        "deviations": [],
    },
    {
        "id": "SUB-CRAH-02", "equipment_tag": "CRAH-05", "spec_section": "23 81 00",
        "vendor": "Blue Star", "model": "BS-PAC120",
        "values": {"sensible_kw": 122, "airflow_m3h": 26000, "ec_fans": True,
                   "supply_temp_control_c": 1.0, "redundancy_n_plus_1": False},
        "deviations": [
            {"clause_ref": "2.2.1", "param": "airflow_m3h", "submitted": "26,000 m3/h", "expected": ">=30,000 m3/h", "severity": "major", "reason": "Airflow below spec; reduced sensible capacity margin at high density."},
            {"clause_ref": "2.5.1", "param": "redundancy_n_plus_1", "submitted": "N configuration", "expected": "N+1 required", "severity": "major", "reason": "Proposal lacks the N+1 redundancy required for Tier III concurrent maintainability."},
        ],
    },
    {
        "id": "SUB-BUSWAY-A", "equipment_tag": "BUSWAY-A", "spec_section": "26 25 00",
        "vendor": "C&S Electric", "model": "CS-Sandwich 4000",
        "values": {"current_rating_a": 4000, "short_circuit_ka": 85, "ip_rating": 54, "tap_off_provision": True},
        "deviations": [
            {"clause_ref": "2.2.1", "param": "short_circuit_ka", "submitted": "85 kA", "expected": ">=100 kA", "severity": "major", "reason": "Short-circuit rating below fault level; requires upstream current limiting."},
            {"clause_ref": "2.3.1", "param": "ip_rating", "submitted": "IP54", "expected": ">=IP55 outdoor", "severity": "minor", "reason": "Ingress protection one grade low for outdoor run between buildings."},
        ],
    },
    {
        "id": "SUB-UPS-A2", "equipment_tag": "UPS-A-02", "spec_section": "26 33 53",
        "vendor": "PowerCore Systems", "model": "PC-Guardian 600",
        "values": {"topology": "double-conversion online", "module_kw": 600, "input_voltage_tolerance_pct": 20,
                   "output_thd_pct": 2.4, "efficiency_pct": 96.5, "battery_autonomy_min": 7,
                   "seismic_cert": True, "factory_witness_test": True},
        "deviations": [],
    },
]

# Critical-path equipment tags — a rejected submittal on these emits a risk_event.
CRITICAL_TAGS = {"SWGR-MV-01"}

# --------------------------------------------------------------------------- #
# Line items (BOQ). Scaled-down stand-in; deck tells the 15k-40k scale story.
# --------------------------------------------------------------------------- #
LINE_ITEMS = [
    ("LI-001", "UPS-A-01", "1000 kW UPS module, double-conversion", "Electrical", "26 33 53", 1, "no", "critical"),
    ("LI-002", "UPS-A-02", "1000 kW UPS module, double-conversion", "Electrical", "26 33 53", 1, "no", "critical"),
    ("LI-003", "UPS-B-01", "1000 kW UPS module, double-conversion", "Electrical", "26 33 53", 1, "no", "high"),
    ("LI-010", "DG-01", "2700 kWe diesel generator set", "Electrical", "26 32 13", 1, "no", "critical"),
    ("LI-011", "DG-02", "2500 kWe diesel generator set", "Electrical", "26 32 13", 1, "no", "high"),
    ("LI-012", "DG-03", "2700 kWe diesel generator set", "Electrical", "26 32 13", 1, "no", "high"),
    ("LI-020", "SWGR-MV-01", "11 kV metal-clad switchgear lineup, 8 panels", "Electrical", "26 13 13", 1, "lot", "critical"),
    ("LI-030", "CRAH-01", "130 kW CRAH unit", "Mechanical", "23 81 00", 6, "no", "high"),
    ("LI-031", "CRAH-05", "120 kW CRAH unit (alt)", "Mechanical", "23 81 00", 2, "no", "normal"),
    ("LI-040", "BUSWAY-A", "4000 A sandwich busway run, IT block", "Electrical", "26 25 00", 120, "m", "high"),
    ("LI-041", "BUSWAY-B", "4000 A sandwich busway run, utility block", "Electrical", "26 25 00", 80, "m", "normal"),
]

# --------------------------------------------------------------------------- #
# Schedule (finish-to-start). Critical path runs through MV switchgear:
#   SWGR submittal -> approval -> manufacture -> delivery -> install -> energize
#   -> integrated (L4) -> IST (L5) -> handover.
# durations in calendar days. Dates are computed by the CPM engine at seed time.
# --------------------------------------------------------------------------- #
SCHEDULE = [
    ("T-000", "1", "Project mobilisation", 10, [], "PMO"),
    ("T-010", "2.1", "MV room civil & builders work", 45, ["T-000"], "Civil"),
    ("T-020", "3.1", "MV switchgear submittal & approval", 25, ["T-000"], "Electrical"),
    ("T-021", "3.2", "MV switchgear manufacture", 90, ["T-020"], "Vendor"),
    ("T-022", "3.3", "MV switchgear delivery to site", 21, ["T-021"], "Logistics"),
    ("T-023", "3.4", "MV switchgear installation", 20, ["T-022", "T-010"], "Electrical"),
    ("T-030", "4.1", "UPS submittal & approval", 20, ["T-000"], "Electrical"),
    ("T-031", "4.2", "UPS manufacture & delivery", 70, ["T-030"], "Vendor"),
    ("T-032", "4.3", "UPS room fit-out & install", 25, ["T-031", "T-010"], "Electrical"),
    ("T-040", "5.1", "Genset submittal & approval", 20, ["T-000"], "Electrical"),
    ("T-041", "5.2", "Genset manufacture & delivery", 80, ["T-040"], "Vendor"),
    ("T-042", "5.3", "Genset install & fuel system", 30, ["T-041", "T-010"], "Mechanical"),
    ("T-050", "6.1", "CRAH submittal & approval", 18, ["T-000"], "Mechanical"),
    ("T-051", "6.2", "CRAH manufacture & delivery", 60, ["T-050"], "Vendor"),
    ("T-052", "6.3", "CRAH install & piping", 28, ["T-051", "T-010"], "Mechanical"),
    ("T-060", "7.1", "Busway fabrication & delivery", 55, ["T-030"], "Vendor"),
    ("T-061", "7.2", "Busway installation", 22, ["T-060", "T-032"], "Electrical"),
    ("T-070", "8.1", "MV energization (L3)", 7, ["T-023"], "Cx"),
    ("T-071", "8.2", "LV distribution energization", 10, ["T-070", "T-061"], "Cx"),
    ("T-080", "9.1", "Genset load bank test (L3)", 6, ["T-042", "T-070"], "Cx"),
    ("T-081", "9.2", "UPS battery discharge test (L3)", 5, ["T-032", "T-071"], "Cx"),
    ("T-082", "9.3", "CRAH functional test (L3)", 5, ["T-052", "T-071"], "Cx"),
    ("T-090", "10.1", "Integrated systems test — L4", 14, ["T-080", "T-081", "T-082"], "Cx"),
    ("T-091", "10.2", "Integrated systems test — L5 (IST / pull-the-plug)", 12, ["T-090"], "Cx"),
    ("T-100", "11.1", "Snagging & documentation", 15, ["T-091"], "PMO"),
    ("T-101", "11.2", "Client handover & Tier III cert evidence", 8, ["T-100"], "PMO"),
]

# --------------------------------------------------------------------------- #
# Procurement + shipments. Seed 3 at-risk (port, vendor slip, customs).
# The switchgear shipment slip is the demo headline (it hits the critical path).
# --------------------------------------------------------------------------- #
PROCUREMENT = [
    # (po_id, line_item_id, vendor, po_date, promised_date, status, submittal_doc_id)
    ("PO-001", "LI-001", "PowerCore Systems", "2026-02-10", "2026-05-20", "delivered", "SUB-UPS-A"),
    ("PO-002", "LI-002", "PowerCore Systems", "2026-02-10", "2026-05-20", "in_transit", "SUB-UPS-A2"),
    ("PO-003", "LI-003", "ELGI Power", "2026-02-15", "2026-06-01", "on_hold", "SUB-UPS-B"),
    ("PO-010", "LI-010", "Kirloskar Green", "2026-02-20", "2026-06-15", "in_transit", "SUB-DG-01"),
    ("PO-011", "LI-011", "Mahindra Powerol", "2026-02-20", "2026-06-20", "on_hold", "SUB-DG-02"),
    ("PO-020", "LI-020", "Schneider Electric", "2026-02-25", "2026-07-05", "at_risk", "SUB-SWGR-01"),
    ("PO-030", "LI-030", "STULZ India", "2026-03-01", "2026-06-10", "delivered", "SUB-CRAH-01"),
    ("PO-040", "LI-040", "C&S Electric", "2026-03-05", "2026-06-25", "in_transit", "SUB-BUSWAY-A"),
]

SHIPMENTS = [
    # (ship_id, po_id, description, origin, lat, lng, eta, required_on_site, status, tier_supplier)
    ("SHP-001", "PO-002", "UPS-A-02 module", "Pune, IN", 18.5204, 73.8567, "2026-07-22", "2026-07-25", "on_track", "PowerCore Systems"),
    ("SHP-010", "PO-010", "DG-01 genset", "Pune, IN", 18.5204, 73.8567, "2026-07-20", "2026-07-28", "on_track", "Kirloskar Green"),
    ("SHP-020", "PO-020", "MV switchgear lineup (8 panels)", "Chennai Port, IN", 13.0827, 80.2707, "2026-08-05", "2026-07-18", "delayed", "Schneider Electric"),
    ("SHP-040", "PO-040", "Busway sections IT block", "Delhi, IN", 28.7041, 77.1025, "2026-07-24", "2026-08-01", "customs_hold", "C&S Electric"),
]

# --------------------------------------------------------------------------- #
# RFIs — historical Q&A with a couple of near-duplicates for the "similar RFI"
# retrieval feature.
# --------------------------------------------------------------------------- #
RFIS = [
    ("RFI-001", "What input voltage window is required for the UPS on the Meghdoot MV supply?",
     "Per spec 26 33 53 clause 2.3.1 the UPS must operate across +/-15% of nominal input without discharging the battery. Submittals showing +/-10% are non-compliant.",
     "Electrical", ["26 33 53"], "answered"),
    ("RFI-002", "Is N+1 redundancy mandatory for the CRAH units in Data Hall A?",
     "Yes. Spec 23 81 00 clause 2.5.1 requires N+1 CRAH redundancy per data hall to meet Tier III concurrent maintainability.",
     "Mechanical", ["23 81 00"], "answered"),
    ("RFI-003", "What is the required short-circuit withstand for the 11 kV switchgear?",
     "Spec 26 13 13 clause 2.2.1 requires not less than 25 kA for 3 seconds. The Schneider submittal at 21 kA is a critical deviation and was rejected.",
     "Electrical", ["26 13 13"], "answered"),
    ("RFI-004", "Can we accept a genset with 6 hours of fuel autonomy instead of 8?",
     "No. Spec 26 32 13 clause 2.2.1 requires 8 hours minimum at prime load. A concession would need client sign-off and an external bulk-fuel contingency plan.",
     "Electrical", ["26 32 13"], "answered"),
    ("RFI-005", "Who approved the revised busway routing between the IT and utility blocks?",
     "The revised routing was agreed in the 2026-05-14 coordination meeting (MoM-03) by the client's engineering rep and the EPC electrical lead, subject to IP55 rating on the outdoor run.",
     "Electrical", ["26 25 00"], "answered"),
    ("RFI-006", "What voltage tolerance must the uninterruptible power supply tolerate on the incoming feed?",
     "As per 26 33 53 / 2.3.1, +/-15% of nominal input voltage without battery discharge. This duplicates the intent of RFI-001.",
     "Electrical", ["26 33 53"], "answered"),
    ("RFI-007", "What emission standard applies to the diesel generators at this site?",
     "CPCB IV+ per spec 26 32 13 clause 2.3.1, consistent with current Indian norms for DG sets of this rating.",
     "Electrical", ["26 32 13"], "answered"),
    ("RFI-008", "Is a factory witness test required before UPS shipment?",
     "Yes, spec 26 33 53 clause 3.1.1 makes the FWT with client attendance mandatory prior to dispatch.",
     "Electrical", ["26 33 53"], "answered"),
    ("RFI-009", "What is the busway short-circuit rating requirement?",
     "Spec 26 25 00 clause 2.2.1 requires not less than 100 kA. The C&S submittal at 85 kA needs upstream current limiting or an alternative rating.",
     "Electrical", ["26 25 00"], "answered"),
    ("RFI-010", "What airflow must each CRAH deliver?",
     "Not less than 30,000 m3/h per spec 23 81 00 clause 2.2.1. The Blue Star alt at 26,000 m3/h is below spec.",
     "Mechanical", ["23 81 00"], "answered"),
]

# --------------------------------------------------------------------------- #
# Commissioning test procedures (L3-L5) with acceptance criteria.
#   criteria: [{param, op, target, unit}]
# --------------------------------------------------------------------------- #
TEST_PROCEDURES = [
    {"id": "TP-DG-LB", "system": "Diesel Generator", "level": "L3", "name": "Genset load bank test",
     "standard_ref": "ISO 8528-6 / TIA-942", "acceptance_criteria": [
        {"param": "steady_state_frequency_hz", "op": "between", "target": [49.5, 50.5], "unit": "Hz"},
        {"param": "voltage_regulation_pct", "op": "<=", "target": 1.0, "unit": "%"},
        {"param": "full_load_accept_single_step", "op": "==", "target": True, "unit": ""},
        {"param": "exhaust_temp_c", "op": "<=", "target": 550, "unit": "C"}]},
    {"id": "TP-UPS-BD", "system": "UPS", "level": "L3", "name": "UPS battery discharge (autonomy) test",
     "standard_ref": "IEC 62040-3 / Uptime Tier III", "acceptance_criteria": [
        {"param": "autonomy_minutes", "op": ">=", "target": 5, "unit": "min"},
        {"param": "final_cell_voltage_v", "op": ">=", "target": 1.75, "unit": "V/cell"},
        {"param": "load_transfer_break_ms", "op": "==", "target": 0, "unit": "ms"}]},
    {"id": "TP-CRAH-FT", "system": "CRAH", "level": "L3", "name": "CRAH functional & airflow test",
     "standard_ref": "ASHRAE TC9.9", "acceptance_criteria": [
        {"param": "airflow_m3h", "op": ">=", "target": 30000, "unit": "m3/h"},
        {"param": "supply_temp_deviation_c", "op": "<=", "target": 1.0, "unit": "C"}]},
    {"id": "TP-IST-L5", "system": "Integrated", "level": "L5", "name": "Integrated systems test — pull-the-plug (IST)",
     "standard_ref": "Uptime Tier III IST", "acceptance_criteria": [
        {"param": "it_load_uninterrupted", "op": "==", "target": True, "unit": ""},
        {"param": "genset_start_and_accept_s", "op": "<=", "target": 30, "unit": "s"},
        {"param": "cooling_recovery_min", "op": "<=", "target": 10, "unit": "min"}]},
]

# --------------------------------------------------------------------------- #
# Cross-module wiring.
#   TEST_PROC_TASK  — which schedule task each commissioning test depends on
#                     (drives schedule -> commissioning readiness).
#   SIM_DETECTION   — when SiteMind first *detected* each risk signal, for the
#                     simulation clock ("flagged N weeks before it bites").
# --------------------------------------------------------------------------- #
TEST_PROC_TASK = {
    "TP-DG-LB": "T-080",   # genset load bank
    "TP-UPS-BD": "T-081",  # UPS battery discharge
    "TP-CRAH-FT": "T-082", # CRAH functional
    "TP-IST-L5": "T-091",  # integrated systems test (L5 IST)
}

# Links each schedule task to the equipment type (spec_section) it concerns and
# its phase. This is the backfill for the schedule_tasks.spec_section/phase
# columns and is what lets any shipment/PO/submittal/tag resolve to a task
# generically (repository.resolve_signal_task) instead of hardcoded id maps.
TASK_EQUIPMENT = {
    "T-020": ("26 13 13", "submittal"),  "T-021": ("26 13 13", "manufacture"),
    "T-022": ("26 13 13", "delivery"),   "T-023": ("26 13 13", "install"),
    "T-030": ("26 33 53", "submittal"),  "T-031": ("26 33 53", "delivery"),
    "T-032": ("26 33 53", "install"),
    "T-040": ("26 32 13", "submittal"),  "T-041": ("26 32 13", "delivery"),
    "T-042": ("26 32 13", "install"),
    "T-050": ("23 81 00", "submittal"),  "T-051": ("23 81 00", "delivery"),
    "T-052": ("23 81 00", "install"),
    "T-060": ("26 25 00", "delivery"),   "T-061": ("26 25 00", "install"),
}

SIM_DETECTION = {
    # ref -> {detected_on, source, title}. bites_on is computed from the data.
    "SHP-020": {"detected_on": "2026-06-05", "source": "supply",
                "title": "MV switchgear delivery slip (Chennai port)"},
    "SUB-SWGR-01": {"detected_on": "2026-06-20", "source": "compliance",
                    "title": "MV switchgear submittal rejected (21 kA < 25 kA)"},
    "SHP-040": {"detected_on": "2026-07-08", "source": "supply",
                "title": "Busway customs hold (Delhi)"},
}

# --------------------------------------------------------------------------- #
# Free-text docs for RAG breadth (meeting minutes / change orders).
# --------------------------------------------------------------------------- #
NARRATIVE_DOCS = [
    {"id": "MoM-03", "type": "meeting_minutes", "title": "Coordination meeting minutes 2026-05-14", "discipline": "Multi",
     "content": "Coordination Meeting MoM-03, 14 May 2026, Project Meghdoot.\nPresent: Client engineering rep, EPC electrical lead, mechanical lead, PMO.\n1. Busway routing between IT and utility blocks revised to avoid the new fire tank foundation. Client and EPC electrical lead agreed the revised outdoor route subject to IP55 rating on exposed sections (ref spec 26 25 00 / 2.3.1). Action: update busway shop drawings.\n2. MV switchgear delivery flagged as schedule concern; vendor Schneider indicated a possible slip from the Chennai port. PMO to track.\n3. UPS-B submittal from ELGI Power noted as non-compliant on input voltage window and efficiency; electrical lead to issue rejection.\n4. Genset fuel autonomy for DG-02 (Mahindra) raised — 6 h submitted vs 8 h required; concession not granted."},
    {"id": "CO-002", "type": "change_order", "title": "Change Order CO-002 — Busway reroute", "discipline": "Electrical",
     "content": "Change Order CO-002. Reroute of 4000 A busway between IT block and utility block per MoM-03 (2026-05-14). Adds 18 m of run and two additional supports. Requires IP55 on the outdoor section per spec 26 25 00 clause 2.3.1. Cost impact: +INR 9.4 lakh. Schedule impact: nil if fabricated in the current window. Approved by client engineering rep."},
    {"id": "MoM-04", "type": "meeting_minutes", "title": "Commissioning readiness review 2026-07-02", "discipline": "Cx",
     "content": "Commissioning Readiness Review, 2 July 2026.\n1. L3 energization sequence depends on MV switchgear installation, which depends on switchgear delivery. Delivery now forecast 5 Aug against a 18 Jul required-on-site date — a three-week exposure to the L4/L5 integrated test window.\n2. UPS and genset are on track for their L3 tests.\n3. CRAH-01 (STULZ) delivered and installed; Blue Star alt units held pending N+1 clarification.\n4. Action: procurement to evaluate air-freight or an alternate switchgear source to protect the energization date."},
]
