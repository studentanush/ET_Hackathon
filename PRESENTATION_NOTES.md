# SiteMind — Presentation Notes

## 5a. Slide: "AI proposes, deterministic engines verify"

**Thesis:** SiteMind never lets the LLM be the final authority on a number, a
date, or a pass/fail. The model proposes and explains; deterministic code
verifies and decides.

- **Schedule mitigations are re-checked by the CPM engine, not trusted from the
  model.** In `schedule_risk.analyze_risks()`, every mitigation the LLM proposes
  is fed back through `cpm.what_if()` and its recovery is recomputed from the
  actual project-slip math before it is ever shown
  (`wi = what_if(conn, m_task, …); m.schedule_recovery_days = max(0, min(r.impact_days, recovered))`).
  The model proposes "air-freight the switchgear"; the math decides how many days
  that actually recovers.

- **Commissioning pass/fail never calls an LLM.** `commissioning.validate()`
  compares each reading to its acceptance criterion with a pure numeric function,
  `_cmp(reading, op, target)` (`>=`, `<=`, `==`, `between`). A model cannot pass a
  failing safety-critical test — by construction, there is no LLM in that path.

- **Compliance findings are schema-validated structured output, not free text.**
  The compliance agent returns a Pydantic `ComplianceReport` via
  `llm.complete_json()`, which validates the JSON against the schema (with a
  retry/repair loop). Every finding has a typed verdict/severity/clause_ref —
  machine-checkable, which is exactly what makes the precision/recall evaluation
  possible.

**One-liner for the slide:** *LLMs for judgment and language; deterministic
engines (networkx CPM, numeric comparators, schema validation) for anything that
must be correct.*

---

## 5b. Honest answers to likely questions

**Q: "Is your retrieval real hybrid search / BM25?"**
Not full BM25, and we don't claim it is. `repository.vector_search()` does dense
retrieval — cosine similarity over local `fastembed` (bge-small) embeddings,
computed as a dot product because the vectors are unit-normalized — plus a light
lexical bonus (a small fixed increment per query keyword that appears in the
chunk). So it's cosine-primary with a lexical tie-breaker, not a tuned BM25 +
dense reranker. At our corpus size (tens of docs, a few thousand chunks) that's
enough for accurate, cited retrieval; the honest production upgrade is a real
BM25/tsvector stage plus a cross-encoder reranker, which is a swap behind the same
repository interface.

**Q: "Is the knowledge graph a real graph database?"**
No — and it doesn't need to be for what it does. `crossmodule.build_graph()`
derives an explicit typed graph (Equipment / Vendor / Task / Document /
TestProcedure / NCR / RiskEvent nodes, with typed edges like `governed_by`,
`scheduled_as`, `affects`, `raised_against`) at read time from the existing
relational tables (foreign keys, spec-section links, task predecessors,
risk→affected_tasks). It's a live projection of the relational spine, not a
persisted Neo4j-style store. The relationships are real and already in the data;
the graph view just makes them explicit. A dedicated graph database would help
only once we need multi-hop graph queries at scale — it wouldn't change what's
shown today.

**Q: "Is your compliance eval overfit to your own ground truth?"**
Fair challenge, and we're explicit about it in the UI ("vs seeded ground truth").
The current evaluation is 23 synthetic submittals with 24 labelled deviations
that we authored, spread across all five equipment types and varied across which
clause is violated — so it's not a single failure mode, and it's large enough to
be non-trivial (current result ~0.92 precision / 1.00 recall / 0.96 F1, with the
two false positives being one explainable boundary case). But it is still our
data and our labels: a real validation study would need actual vendor submittal
documents (PDFs with the messiness of real datasheets), specs we didn't write,
and a held-out label set annotated by someone outside the team — ideally a
practicing QA engineer — so the model is graded against ground truth it and we
never shaped.
