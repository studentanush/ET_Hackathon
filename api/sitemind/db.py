"""SQLite data spine.

The plan specced Postgres + pgvector. We keep the *same logical schema* but
store vectors as float32 BLOBs and do brute-force cosine in numpy (see
repository.vector_search). At demo scale (~a few thousand chunks) this is
instant; the production path to pgvector is a repository swap, nothing else.

Arrays/jsonb from the Postgres schema become JSON TEXT here.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,          -- spec|submittal|drawing|rfi|meeting_minutes|change_order|standard
    title       TEXT NOT NULL,
    discipline  TEXT,
    revision    TEXT,
    file_path   TEXT,
    content     TEXT,                   -- full synthetic text (no real files on disk)
    uploaded_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id),
    seq         INTEGER,
    text        TEXT,
    embedding   BLOB,                   -- float32[EMBED_DIM]
    page        INTEGER,
    section_ref TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);

CREATE TABLE IF NOT EXISTS line_items (
    id          TEXT PRIMARY KEY,
    tag         TEXT,
    description TEXT,
    discipline  TEXT,
    spec_section TEXT,
    qty         REAL,
    unit        TEXT,
    criticality TEXT                    -- critical|high|normal
);

CREATE TABLE IF NOT EXISTS procurement_orders (
    id            TEXT PRIMARY KEY,
    line_item_id  TEXT REFERENCES line_items(id),
    vendor        TEXT,
    po_date       TEXT,
    promised_date TEXT,
    status        TEXT,
    submittal_doc_id TEXT REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS shipments (
    id             TEXT PRIMARY KEY,
    po_id          TEXT REFERENCES procurement_orders(id),
    description    TEXT,
    origin         TEXT,
    current_lat    REAL,
    current_lng    REAL,
    eta            TEXT,
    required_on_site TEXT,
    status         TEXT,
    tier_supplier  TEXT
);

CREATE TABLE IF NOT EXISTS schedule_tasks (
    id            TEXT PRIMARY KEY,
    wbs           TEXT,
    name          TEXT,
    duration_days INTEGER,
    planned_start TEXT,
    planned_end   TEXT,
    actual_start  TEXT,
    actual_end    TEXT,
    predecessors  TEXT,                 -- JSON array of task ids
    resource      TEXT,
    is_critical   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS test_procedures (
    id                  TEXT PRIMARY KEY,
    system              TEXT,
    level               TEXT,           -- L1..L5
    name                TEXT,
    acceptance_criteria TEXT,           -- JSON array of {param,operator,target,unit}
    standard_ref        TEXT
);

CREATE TABLE IF NOT EXISTS test_records (
    id           TEXT PRIMARY KEY,
    procedure_id TEXT REFERENCES test_procedures(id),
    executed_by  TEXT,
    executed_at  TEXT,
    readings     TEXT,                  -- JSON
    result       TEXT,                  -- PASS|FAIL
    ncr_id       TEXT
);

CREATE TABLE IF NOT EXISTS ncrs (
    id            TEXT PRIMARY KEY,
    source_module TEXT,
    severity      TEXT,                 -- minor|major|critical
    description   TEXT,
    spec_citation TEXT,
    equipment_tag TEXT,
    status        TEXT,                 -- open|closed
    raised_at     TEXT
);

CREATE TABLE IF NOT EXISTS rfis (
    id          TEXT PRIMARY KEY,
    number      TEXT,
    question    TEXT,
    answer      TEXT,
    discipline  TEXT,
    spec_refs   TEXT,                   -- JSON array
    status      TEXT,
    raised_at   TEXT,
    answered_at TEXT
);

CREATE TABLE IF NOT EXISTS risk_events (
    id                TEXT PRIMARY KEY,
    source_module     TEXT,
    risk_type         TEXT,
    title             TEXT,
    description       TEXT,
    probability       REAL,
    impact_days       INTEGER,
    affected_tasks    TEXT,             -- JSON array of task ids
    detected_at       TEXT,
    mitigation_options TEXT,            -- JSON
    status            TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    actor     TEXT,
    action    TEXT,
    entity    TEXT,
    entity_id TEXT,
    detail    TEXT,
    at        TEXT
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or config.DB_PATH
    conn = sqlite3.connect(p, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(path: Path | None = None) -> None:
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def reset_db(path: Path | None = None) -> None:
    """Drop everything and recreate — used by the demo reset endpoint."""
    p = path or config.DB_PATH
    conn = connect(p)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for r in rows:
            conn.execute(f"DROP TABLE IF EXISTS {r['name']}")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
