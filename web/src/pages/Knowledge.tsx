import { useState } from "react";
import { apiPost, askStream, type Citation } from "../lib/api";
import { Card, Button, Badge, Banner, Spinner, PageHeader } from "../components/ui";

const SAMPLES = [
  "What input voltage tolerance must the UPS handle?",
  "Is N+1 redundancy required for the CRAH units?",
  "Who approved the busway reroute and when?",
];

export default function Knowledge() {
  return (
    <div className="space-y-5">
      <PageHeader title="Project Knowledge & RFI Intelligence">
        RAG chat over all project documents with mandatory citations, plus similar-RFI retrieval and
        auto-drafted answers.
      </PageHeader>
      <div className="grid gap-5 lg:grid-cols-2">
        <AskPanel />
        <RfiPanel />
      </div>
    </div>
  );
}

function AskPanel() {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState("");
  const [cites, setCites] = useState<Citation[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function ask(question: string) {
    if (!question.trim()) return;
    setBusy(true);
    setErr(null);
    setAnswer("");
    setCites([]);
    try {
      await askStream(
        question,
        (c) => setCites(c),
        (t) => setAnswer((a) => a + t),
      );
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Ask the project">
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask(q)}
          placeholder="e.g. Does the Schneider switchgear meet the fault rating?"
          className="flex-1 rounded-lg border border-line bg-surface2 px-3 py-2 text-[13px] outline-none focus:border-accent"
        />
        <Button onClick={() => ask(q)} disabled={busy}>
          Ask
        </Button>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button
            key={s}
            onClick={() => {
              setQ(s);
              ask(s);
            }}
            className="rounded-md border border-accent/40 px-2 py-1 text-[11px] text-accent hover:bg-accent/10"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="mt-4 min-h-[80px]">
        {busy && !answer && <Spinner label="Retrieving & answering…" />}
        {err && <Banner tone="bad">{err}</Banner>}
        {answer && (
          <div className="rounded-lg border border-line bg-surface2 px-4 py-3 text-[13.5px] leading-relaxed whitespace-pre-wrap">
            {answer}
            {cites.length > 0 && (
              <div className="mt-3 text-[12px] text-mut">
                Sources:{" "}
                {cites.map((c) => (
                  <span key={c.doc_id} className="mr-1.5 font-mono text-accent">
                    [{c.doc_id}]
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

function RfiPanel() {
  const [q, setQ] = useState("What voltage window must the UPS tolerate on the incoming feed?");
  const [res, setRes] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function draft() {
    setBusy(true);
    setErr(null);
    setRes(null);
    try {
      setRes(await apiPost("/rfi/draft", { question: q }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Draft a new RFI">
      <textarea
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="h-16 w-full rounded-lg border border-line bg-surface2 px-3 py-2 text-[13px] outline-none focus:border-accent"
      />
      <div className="mt-2">
        <Button onClick={draft} disabled={busy}>
          Find similar & draft answer
        </Button>
      </div>
      <div className="mt-3 space-y-2">
        {busy && <Spinner label="Retrieving similar RFIs…" />}
        {err && <Banner tone="bad">{err}</Banner>}
        {res && (
          <>
            {res.best_match && (
              <Banner tone={res.deflected ? "good" : "info"}>
                {res.deflected ? "✓ Likely deflected — " : ""}Closest prior:{" "}
                <b>{res.best_match.number}</b> (similarity{" "}
                {(res.best_match.similarity * 100).toFixed(0)}%)
              </Banner>
            )}
            <div className="rounded-lg border border-line bg-surface2 px-4 py-3 text-[13px] leading-relaxed whitespace-pre-wrap">
              {res.draft_answer}
            </div>
            <div className="text-[11px] text-faint">
              Similar:{" "}
              {res.similar_rfis
                .map((s: any) => `${s.number} (${(s.similarity * 100).toFixed(0)}%)`)
                .join(", ")}
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
