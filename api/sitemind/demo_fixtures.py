"""Static demo inputs. Not part of canonical.SPECS — used by the Spec Compiler
demo so the compilation step does real work on unstructured prose.
"""

# A fire-suppression spec written the way a real spec document reads (narrative
# prose, not a list of {param, op, value} facts). The compiler must extract the
# structured requirements from this.
FIRE_SUPPRESSION_SPEC = """SECTION 21 13 00 — CLEAN AGENT FIRE SUPPRESSION SYSTEM

PART 2 — PRODUCTS

The clean agent fire suppression system shall protect the data hall and
associated electrical rooms. The extinguishing agent shall be inert gas or a
chemical clean agent that is electrically non-conductive and leaves no residue.
The system shall achieve the design extinguishing concentration throughout the
protected volume within 10 seconds of agent release, in accordance with
NFPA 2001.

Agent storage cylinders shall provide not less than 30 seconds of discharge
duration at the design concentration. The design concentration shall not exceed
the No Observed Adverse Effect Level (NOAEL) for occupied spaces, so that the
space remains safe for personnel during discharge.

Detection shall be by a cross-zoned (double-knock) very early smoke detection
arrangement; a single detector shall not be capable of initiating agent release.
The system shall provide a pre-discharge alarm with a minimum 30 second delay
before agent release to allow personnel to evacuate and to permit an abort.

The control panel shall be listed to UL 864 and shall be fully addressable. Room
integrity (fan) testing to confirm the enclosure can hold the agent concentration
for a retention time of at least 10 minutes is mandatory prior to acceptance.

PART 3 — EXECUTION

The installer shall be certified by the agent manufacturer, and complete
as-built drawings and a room integrity test report shall be submitted before
handover."""
