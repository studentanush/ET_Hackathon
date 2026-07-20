import { useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import {
  Card,
  Button,
  Badge,
  Banner,
  Spinner,
  Table,
  Td,
  PageHeader,
  useAsync,
} from "../components/ui";

const verdictTone: Record<string, string> = {
  DEVIATION: "dev",
  UNCLEAR: "warn",
  COMPLIANT: "ok",
};

export default function Compliance() {
  const subs = useAsync<any[]>(() => apiGet("/compliance/submittals"));
  const [sel, setSel] = useState("SUB-SWGR-01");
  const [busy, setBusy] = useState<null | "check" | "eval">(null);
  const [result, setResult] = useState<any>(null);
  const [evalR, setEvalR] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function runCheck() {
    setBusy("check");
    setErr(null);
    setEvalR(null);
    try {
      setResult(await apiPost("/compliance/check", { submittal_doc_id: sel }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  }
  async function runEval(refresh: boolean) {
    setBusy("eval");
    setErr(null);
    setResult(null);
    try {
      setEvalR(await apiPost(`/compliance/evaluate${refresh ? "?refresh=true" : ""}`));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Spec & Quality Compliance Agent">
        Auto-checks a vendor submittal against the governing specification clause-by-clause.
        Deviations raise NCRs; a critical-path item also emits a schedule risk (cross-module).
      </PageHeader>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={sel}
            onChange={(e) => setSel(e.target.value)}
            className="rounded-lg border border-line bg-surface2 px-3 py-2 text-[13px]"
          >
            {subs.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.tag} · {s.spec_section} · {s.vendor} ({s.seeded_deviations} seeded)
              </option>
            ))}
          </select>
          <Button onClick={runCheck} disabled={!!busy}>
            {busy === "check" ? "Checking…" : "Run compliance check"}
          </Button>
          <Button variant="ghost" onClick={() => runEval(false)} disabled={!!busy}>
            {busy === "eval" ? "Loading…" : "Show accuracy evaluation"}
          </Button>
        </div>

        <div className="mt-4">
          {busy === "check" && <Spinner label="Retrieving spec clauses & comparing…" />}
          {busy === "eval" && <Spinner label="Loading accuracy evaluation…" />}
          {err && <Banner tone="bad">{err}</Banner>}

          {result && !busy && <CheckResult r={result} />}
          {evalR && !busy && <EvalResult r={evalR} onRefresh={() => runEval(true)} />}
        </div>
      </Card>
    </div>
  );
}

function CheckResult({ r }: { r: any }) {
  const rep = r.report;
  return (
    <div className="space-y-3">
      <Banner tone={rep.summary_verdict === "COMPLIANT" ? "good" : "bad"}>
        {rep.equipment_tag} — {rep.summary_verdict.replace("_", " ")} · spec {rep.spec_section} · ~
        {rep.review_time_saved_hours}h saved vs manual review
      </Banner>
      {r.risk_event && (
        <Banner tone="bad">
          ⚡ Cross-module: critical-path risk raised → <b>{r.risk_event.title}</b> (
          {r.risk_event.impact_days}d impact). Now visible in Schedule Risk.
        </Banner>
      )}
      <Table head={["Clause", "Requirement", "Submitted", "Verdict", "Sev", "Action"]}>
        {rep.findings.map((f: any, i: number) => (
          <tr key={i}>
            <Td className="font-mono">{f.clause_ref}</Td>
            <Td>{f.requirement.slice(0, 58)}</Td>
            <Td>{f.submittal_value}</Td>
            <Td>
              <Badge tone={verdictTone[f.verdict]}>{f.verdict}</Badge>
            </Td>
            <Td>{f.severity !== "none" && <Badge tone={f.severity}>{f.severity}</Badge>}</Td>
            <Td className="text-mut">{f.recommended_action?.slice(0, 46)}</Td>
          </tr>
        ))}
      </Table>
      {r.ncrs?.length > 0 && (
        <p className="text-[12px] text-mut">
          NCRs auto-raised:{" "}
          {r.ncrs.map((n: any) => (
            <span key={n.id} className="mr-2 font-mono text-accent">
              {n.id}
            </span>
          ))}
        </p>
      )}
    </div>
  );
}

function EvalResult({ r, onRefresh }: { r: any; onRefresh: () => void }) {
  return (
    <div className="space-y-3">
      <Banner tone="good">
        Precision {(r.precision * 100).toFixed(0)}% · Recall {(r.recall * 100).toFixed(0)}% · F1{" "}
        {(r.f1 * 100).toFixed(0)}% — vs seeded ground truth (TP {r.true_positives} / FP{" "}
        {r.false_positives} / FN {r.false_negatives}){" "}
        <span className="font-normal text-mut">
          · {r.cached ? "pre-computed over the labelled test set" : "computed live"}
        </span>
      </Banner>
      <Table head={["Submittal", "Expected deviations", "Flagged", "TP/FP/FN", "Verdict"]}>
        {r.per_document.map((d: any) => (
          <tr key={d.submittal}>
            <Td>{d.tag}</Td>
            <Td className="font-mono">{d.expected.join(", ") || "—"}</Td>
            <Td className="font-mono">{d.flagged.join(", ") || "—"}</Td>
            <Td>
              {d.tp}/{d.fp}/{d.fn}
            </Td>
            <Td>
              <Badge tone={d.verdict === "COMPLIANT" ? "ok" : "dev"}>{d.verdict}</Badge>
            </Td>
          </tr>
        ))}
      </Table>
      <div className="flex items-center gap-3">
        <Button variant="ghost" onClick={onRefresh}>
          Re-run live (~2 min)
        </Button>
        <span className="text-[12px] text-mut">
          Labelled set: 9 submittals, 10 seeded deviations (ground truth in canonical.py).
        </span>
      </div>
    </div>
  );
}
