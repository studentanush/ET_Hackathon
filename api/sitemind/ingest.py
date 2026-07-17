"""Ingestion: text -> chunks -> embeddings -> chunks table.

Idempotent per document (deletes existing chunks for the doc id first), so it
doubles as the live-upload path (POST /ingest) in the demo.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import embeddings


def _chunk_prose(text: str, target_chars: int = 900, overlap: int = 150) -> list[str]:
    """Paragraph-aware chunking with light overlap for continuity."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 1 <= target_chars:
            buf = f"{buf}\n{p}" if buf else p
        else:
            if buf:
                chunks.append(buf)
            buf = (buf[-overlap:] + "\n" + p) if buf else p
    if buf:
        chunks.append(buf)
    return chunks or [text]


def upsert_document(
    conn,
    *,
    doc_id: str,
    doc_type: str,
    title: str,
    content: str,
    discipline: str | None = None,
    revision: str | None = None,
    prechunked: list[dict] | None = None,
) -> int:
    """Store/replace a document and its embedded chunks. Returns chunk count.

    `prechunked` lets callers supply their own chunks with section_ref/page
    (used for specs so each clause is its own citable chunk). Otherwise the
    content is prose-chunked.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO documents (id, type, title, discipline, revision, file_path, content, uploaded_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (doc_id, doc_type, title, discipline, revision, f"synthetic://{doc_id}", content, now),
    )
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))

    if prechunked:
        items = prechunked
    else:
        items = [{"text": t} for t in _chunk_prose(content)]

    texts = [it["text"] for it in items]
    vecs = embeddings.embed(texts)
    for seq, (it, vec) in enumerate(zip(items, vecs)):
        conn.execute(
            "INSERT INTO chunks (document_id, seq, text, embedding, page, section_ref) "
            "VALUES (?,?,?,?,?,?)",
            (doc_id, seq, it["text"], embeddings.to_blob(vec),
             it.get("page"), it.get("section_ref")),
        )
    conn.commit()
    return len(items)
