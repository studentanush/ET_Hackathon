"""Project Knowledge & RFI Intelligence (flagship #3).

RAG chat with mandatory citations over all project documents, plus similar-RFI
retrieval and auto-drafted RFI answers.
"""
from __future__ import annotations

from typing import Iterator

from .. import llm, repository

SYS = (
    "You are the project knowledge assistant for a data-centre EPC build. Answer "
    "ONLY from the provided context passages. Every factual claim must cite its "
    "source as [doc_id]. If the context does not contain the answer, say you do "
    "not have that information — do not invent. Be concise and specific (quote spec "
    "clause numbers and values where relevant)."
)


def _context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['document_id']}] (section {c.get('section_ref') or '-'}, {c['type']})\n{c['text']}"
        for c in chunks
    )


def retrieve(conn, question: str, k: int = 6) -> list[dict]:
    return repository.vector_search(conn, question, k=k)


def ask(conn, question: str, *, k: int = 6, effort: str = "high") -> dict:
    chunks = retrieve(conn, question, k)
    msgs = [
        {"role": "system", "content": SYS},
        {"role": "user", "content": f"CONTEXT:\n{_context(chunks)}\n\nQUESTION: {question}"},
    ]
    answer = llm.complete(msgs, effort=effort, max_tokens=900)
    citations = [
        {"doc_id": c["document_id"], "title": c["title"], "section_ref": c.get("section_ref"),
         "type": c["type"], "score": round(c["score"], 3)}
        for c in chunks
    ]
    return {"answer": answer, "citations": citations}


def ask_stream(conn, question: str, *, k: int = 6, effort: str = "high") -> tuple[Iterator[str], list[dict]]:
    chunks = retrieve(conn, question, k)
    msgs = [
        {"role": "system", "content": SYS},
        {"role": "user", "content": f"CONTEXT:\n{_context(chunks)}\n\nQUESTION: {question}"},
    ]
    citations = [
        {"doc_id": c["document_id"], "title": c["title"], "section_ref": c.get("section_ref"),
         "type": c["type"], "score": round(c["score"], 3)}
        for c in chunks
    ]
    return llm.stream(msgs, effort=effort, max_tokens=900), citations


def draft_rfi(conn, question: str, *, effort: str = "high") -> dict:
    """Find similar historical RFIs and auto-draft an answer with citations."""
    similar = repository.find_similar_rfis(conn, question, k=4)
    best = similar[0] if similar else None
    ctx_chunks = retrieve(conn, question, k=5)
    similar_txt = "\n".join(
        f"[{r['number']}] Q: {r['question']}\n   A: {r['answer']} (refs {', '.join(r['spec_refs'])})"
        for r in similar
    )
    msgs = [
        {"role": "system", "content":
            "You draft answers to new RFIs for a data-centre EPC project using prior "
            "RFIs and spec context. Cite sources as [doc_id]. If a prior RFI already "
            "answers this, base your draft on it and note the reference."},
        {"role": "user", "content":
            f"PRIOR SIMILAR RFIs:\n{similar_txt}\n\nSPEC CONTEXT:\n{_context(ctx_chunks)}\n\n"
            f"NEW RFI QUESTION: {question}\n\nDraft a concise answer with citations."},
    ]
    draft = llm.complete(msgs, effort=effort, max_tokens=600)
    return {
        "draft_answer": draft,
        "best_match": ({"number": best["number"], "question": best["question"],
                        "similarity": round(best["similarity"], 3)} if best else None),
        "similar_rfis": [
            {"number": r["number"], "question": r["question"], "similarity": round(r["similarity"], 3)}
            for r in similar
        ],
        "deflected": bool(best and best["similarity"] > 0.75),
    }
