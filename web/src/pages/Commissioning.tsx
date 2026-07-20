import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { Card, Button, Badge, Banner, Spinner, Table, Td, PageHeader, useAsync } from "../components/ui";

export default function Commissioning() {
  const procs = useAsync<any[]>(() => apiGet("/commissioning/procedures"));
  const ready = useAsync<any[]>(() => apiGet("/commissioning/readiness"));
  const [pid, setPid] = useState<string>("");
  const [readings, setReadings] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const proc = procs.data?.find((p) => p.id === pid) || procs.data?.[0];
  useEffect(() => {
    if (procs.data && !pid) setPid(procs.data[0].id);
  }, [procs.data]);
  useEffect(() => {
    setReadings({});
    setResult(null);
  }, [pid]);

  function fillFail() {
    if (!proc) return;
    const r: Record<string, any> = {};
    proc.acceptance_criteria.forEach((c: any, i: number) => {
      if (typeof c.target === "boolean") r[c.param] = true;
      else if (c.op === "between") r[c.param] = i === 0 ? c.target[0] - 2 : (c.target[0] + c.target[1]) / 2;
      else if (c.op === "<=") r[c.param] = i === 0 ? Number(c.target) + (Number(c.target) > 10 ? 10 : 0.5) : c.target;
      else if (c.op === ">=") r[c.param] = i === 0 ? Number(c.target) - (Number(c.target) > 10 ? 4 : 0.5) : c.target;
      else r[c.param] = c.target;
    });
    setReadings(r);
  }

  async function validate() {
    if (!proc) return;
    setBusy(true);
    const payload: Record<string, any> = {};
    proc.acceptance_criteria.forEach((c: any) => {
      let v = readings[c.param];
      if (typeof c.target === "boolean") v = v === true || v === "true";
      else if (v !== undefined && v !== "" && !isNaN(Number(v))) v = Number(v);
      payload[c.param] = v ?? "";
    });
    try {
      setResult(await apiPost("/commissioning/validate", { procedure_id: proc.id, readings: payload }));
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setBusy(false);
    }
  }

  const blocked = (ready.data || []).filter((r) => r.status === "BLOCKED");

  return (
    <div className="space-y-5">
      <PageHeader title="Commissioning Validation Engine">
        Guided test execution. Readings are validated against acceptance criteria (TIA-942 / Uptime
        aligned); a failure auto-raises an NCR and writes the test record. <b>Deterministic by
        design</b> — safety-critical pass/fail is a numeric comparison in code, not an LLM judgment.
      </PageHeader>

      <Card title="Commissioning readiness · schedule → commissioning" pad={false}>
        <div className="p-4 pb-0">
          {ready.loading ? (
            <Spinner />
          ) : blocked.length ? (
            <Banner tone="bad">
              ⚡ Cross-module: {blocked.length} test{blocked.length > 1 ? "s" : ""} BLOCKED by upstream
              schedule risks.
            </Banner>
          ) : (
            <Banner tone="good">
              All tests ready — no blocking risks. Run Compliance or Supply to see blockers appear.
            </Banner>
          )}
        </div>
        <div className="p-4">
          <Table head={["Test", "Level", "Status", "Blocked by"]}>
            {(ready.data || []).map((r) => (
              <tr key={r.procedure_id}>
                <Td>{r.name}</Td>
                <Td>{r.level}</Td>
                <Td>
                  <Badge tone={r.status === "BLOCKED" ? "dev" : "ok"}>{r.status}</Badge>
                </Td>
                <Td className="text-mut">
                  {r.blockers.map((b: any) => `${b.title} (${b.impact_days}d)`).join("; ") || "—"}
                </Td>
              </tr>
            ))}
          </Table>
        </div>
      </Card>

      <Card title="Execute a test">
        {!proc ? (
          <Spinner />
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={pid}
                onChange={(e) => setPid(e.target.value)}
                className="rounded-lg border border-line bg-surface2 px-3 py-2 text-[13px]"
              >
                {procs.data!.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.level} · {p.name}
                  </option>
                ))}
              </select>
              <span className="text-[12px] text-mut">Standard: {proc.standard_ref}</span>
            </div>

            <div className="mt-3">
              <Table head={["Parameter", "Acceptance criteria", "Reading"]}>
                {proc.acceptance_criteria.map((c: any) => {
                  const tgt =
                    c.op === "between" ? `${c.target[0]}..${c.target[1]}` : `${c.op} ${c.target}`;
                  return (
                    <tr key={c.param}>
                      <Td>{c.param}</Td>
                      <Td className="text-mut">
                        {tgt} {c.unit}
                      </Td>
                      <Td>
                        {typeof c.target === "boolean" ? (
                          <select
                            value={String(readings[c.param] ?? "true")}
                            onChange={(e) =>
                              setReadings({ ...readings, [c.param]: e.target.value === "true" })
                            }
                            className="rounded-md border border-line bg-surface2 px-2 py-1"
                          >
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        ) : (
                          <input
                            value={readings[c.param] ?? ""}
                            onChange={(e) => setReadings({ ...readings, [c.param]: e.target.value })}
                            placeholder="reading"
                            className="w-28 rounded-md border border-line bg-surface2 px-2 py-1"
                          />
                        )}
                      </Td>
                    </tr>
                  );
                })}
              </Table>
            </div>

            <div className="mt-3 flex gap-3">
              <Button onClick={validate} disabled={busy}>
                {busy ? "Validating…" : "Validate & generate record"}
              </Button>
              <Button variant="ghost" onClick={fillFail}>
                Demo: enter a failing reading
              </Button>
            </div>

            {result && (
              <div className="mt-4 space-y-2">
                {result.error ? (
                  <Banner tone="bad">{result.error}</Banner>
                ) : (
                  <>
                    <Banner tone={result.overall === "PASS" ? "good" : "bad"}>
                      {result.procedure} — {result.overall} · record {result.record_id}
                      {result.ncr_id ? ` · NCR ${result.ncr_id} raised` : ""}
                    </Banner>
                    <Table head={["Parameter", "Reading", "Target", "Result"]}>
                      {result.steps.map((s: any) => (
                        <tr key={s.param}>
                          <Td>{s.param}</Td>
                          <Td className="font-mono">{s.reading}</Td>
                          <Td className="text-mut">{s.target}</Td>
                          <Td>
                            <Badge tone={s.result === "PASS" ? "ok" : "dev"}>{s.result}</Badge>
                          </Td>
                        </tr>
                      ))}
                    </Table>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
