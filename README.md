# SiteMind — AI Intelligence Platform for Data Centre EPC Delivery

Unifies specifications, schedules, procurement, quality records and RFIs for a
hyperscale data-centre build into one intelligence layer. Built on a synthetic
but internally-consistent project dataset (**Project Meghdoot** — a 24 MW campus
in Navi Mumbai, Phase 1 = one 8 MW data hall).

> Hackathon prototype. Five capabilities on one shared data spine, with agents
> that cross-reference each other's outputs — not five separate chatbots.

---

## Headline results (measured, in-app)

| Metric | Result | How |
|---|---|---|
| **Compliance detection** | **Precision 100% · Recall 100% · F1 100%** | Agent run over 9 submittals with 10 labelled deviations (ground truth in `canonical.py`). Result is cached (`eval_cache.json`) so the demo button is instant; recompute live with `POST /api/compliance/evaluate?refresh=true`. |
| **Schedule risk lead time** | Simulation clock flags the MV-switchgear slip **~6 weeks** before it bites (detected 05-Jun, required-on-site 18-Jul) | CPM what-if verifies the 18-day critical-path slip (finish 2026-08-30 → 2026-09-17). `GET /api/schedule/simulation`. |
| **RFI deflection** | Similar prior RFI retrieved at **>80% similarity**, answer auto-drafted | `POST /api/rfi/draft`. |
| **Review effort** | ~5.5 h → minutes per submittal; shown as a live "hours saved" counter | Dashboard KPI. |

---

## The five modules

1. **Spec & Quality Compliance Agent** (deep) — checks a vendor submittal against
   the governing spec clause-by-clause, structured verdict, auto-raises NCRs, and
   **emits a schedule risk if the item is on the critical path** (the cross-module hook).
2. **Predictive Schedule Risk Engine** (deep) — deterministic CPM core + LLM analyst.
   Every impact and mitigation is **verified by the CPM what-if** — the model never invents dates.
3. **Project Knowledge & RFI Intelligence** (deep) — RAG chat with mandatory citations,
   similar-RFI retrieval, auto-drafted RFI answers.
4. **Supply Chain Visibility** (slice) — map of critical shipments; at-risk items feed the risk engine.
5. **Commissioning Validation Engine** (slice) — deterministic by design (safety-critical pass/fail is a numeric comparison in code, not an LLM judgment); validates readings against acceptance criteria (TIA-942 /
   Uptime aligned), auto-NCR on failure, writes the test record.

**Cross-module intelligence** (the differentiator) — all three hooks wired:
1. **compliance → schedule** — a rejected critical-path submittal raises a schedule risk.
2. **supply → schedule** — an at-risk shipment (ETA later than required-on-site) raises a schedule risk with CPM-computed impact.
3. **schedule → commissioning** — open schedule risks mark downstream commissioning tests BLOCKED (e.g. the L5 IST is blocked because switchgear energization slips).

**Simulation clock**: a timeline slider replays the project week-by-week. Each risk
turns amber when SiteMind first *detects* it and red when it *bites* — the switchgear
delivery slip is flagged **~6 weeks** before it hits the required-on-site date.

**Knowledge graph** (`GET /api/graph`, UI view): the relational spine is projected
into an explicit typed graph — Equipment / Vendor / Task / Document / TestProcedure /
NCR / RiskEvent nodes with typed edges (`governed_by`, `scheduled_as`, `supplied_by`,
`depends_on`, `affects`, `validates`, `raised_against`) — derived from the tables at
read time (~75 nodes / ~100 edges). The "one intelligence graph" is literal, not a
metaphor: click any node to trace its relationships.

---

## Stack (adapted to run on Groq, no paid Claude/pgvector needed)

| Layer | Choice |
|---|---|
| LLM | **Groq** — `llama-3.3-70b-versatile` (agents) + `llama-3.1-8b-instant` (fast). Token-efficient so it stays under the free-tier daily limit; `openai/gpt-oss-120b` also works but its reasoning-token overhead exhausts the 200k/day free quota quickly. |
| Structured output | JSON-mode + Pydantic validation with fallback extraction (`llm.complete_json`) |
| Agent loop | OpenAI-style function-calling loop (`llm.run_agent`) |
| Embeddings | **Local** `fastembed` bge-small-en-v1.5 (384-dim, no API) |
| Vector store | **SQLite** + float32 BLOBs + numpy brute-force cosine (behind a repository layer; pgvector is a drop-in swap) |
| Scheduling | `networkx` CPM (forward/backward pass, float, critical path, what-if) — deterministic |
| API | FastAPI + SSE streaming |
| Frontend | **React + TypeScript + Vite + Tailwind v4** (`web/`) — sidebar dashboard shell, one route per module, reusable components. (A zero-dependency `api/sitemind/static/index.html` fallback is also served by FastAPI at `/`.) |

> The original plan targeted the Claude SDK (native PDF citations, `messages.parse`,
> prompt caching, Batches). On Groq those become: text submittals + chunk-level
> citations, JSON-mode + validation, and plain sequential calls. Architecture,
> determinism, eval and cross-module hooks are unchanged.

---

## Run it

```bash
# 1. deps (uv or pip)
cd api
uv venv --python 3.13 && uv pip install -r requirements.txt
#   (or: python -m venv .venv && .venv/Scripts/pip install -r requirements.txt)

# 2. key — copy .env.example to .env at repo root and set GROQ_API_KEY

# 3. seed the demo database
.venv/Scripts/python -m sitemind.seed

# 4. run the backend API
.venv/Scripts/python -m uvicorn sitemind.main:app --host 127.0.0.1 --port 8141
```

```bash
# 5. run the React frontend (separate terminal)
cd web
npm install
npm run dev            # Vite dev server on http://localhost:5175
# it proxies /api -> http://127.0.0.1:8141 (override with SITEMIND_API env var)
```

Open **http://localhost:5175**. (Or, for a zero-build fallback, just open the API's
own page at http://127.0.0.1:8141 — the legacy single-file UI.)

---

## Demo script (3–5 min) — the scripted click-path for the video

1. **Dashboard** — project health, forecast finish (2026-08-30), open NCRs/risks, hours-saved. "One spine, five modules."
2. **Compliance** → pick **SWGR-MV-01 (Schneider)** → *Run compliance check*.
   - Agent flags clause **2.2.1**: short-circuit 21 kA vs required 25 kA → **NON_COMPLIANT**, NCR raised.
   - Red banner: **critical-path risk raised** → cross-module hook fires.
3. **Compliance** → *Run accuracy evaluation* → **100% precision/recall/F1** on the labelled set. (Technical Excellence.)
4. **Supply Chain** → map of critical shipments; the switchgear is red (ETA 05-Aug vs required 18-Jul).
   - Banner: *cross-module* — the at-risk shipment **auto-raised a schedule risk** (18-day impact).
5. **Schedule Risk** → **Simulation clock**: scrub back to mid-June → switchgear risk shows *"FLAGGED (early warning) · ~4w until impact"*; scrub to today → *"BITING"*. Headline: **flagged ~6 weeks early.**
   - Gantt with critical path in red → *Analyze schedule risks* → ranked register (compliance risk **and** shipment slip), each with **CPM-verified** mitigations.
6. **Knowledge / RFI** → ask *"Does the Schneider switchgear meet the fault rating?"* → streamed answer **with clickable citations** to the spec + submittal.
   - *Draft a new RFI* → similar prior RFI retrieved, answer auto-drafted. (Business Impact: 2 days → 30 s.)
7. **Commissioning** → readiness panel shows *cross-module* — **4 tests BLOCKED** by the upstream switchgear risk. Pick UPS battery discharge → *enter a failing reading* → **FAIL**, auto-NCR, test record written.
8. Back to **Dashboard** → health score, risks, NCRs, hours-saved have all moved. "Every AI claim is clickable to source."

> `↻ Reset demo` restores the clean seeded snapshot between runs.

---

## Layout

```
api/sitemind/
  config.py llm.py embeddings.py db.py repository.py   # spine
  cpm.py                                               # deterministic CPM engine
  crossmodule.py                                       # supply->schedule, schedule->commissioning, simulation clock
  canonical.py docgen.py ingest.py seed.py            # dataset (single source of truth)
  schemas.py                                          # Pydantic structured-output models
  agents/ compliance.py schedule_risk.py rag.py commissioning.py
  main.py static/index.html                           # API + dashboard
```

Everything the demo shows derives from `canonical.py`, so tags / spec sections /
dates cross-reference by construction — and the seeded deviations there are the
labelled ground truth for the accuracy number.
