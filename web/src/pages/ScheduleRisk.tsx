import { useMemo, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { Card, StatTile, Button, Badge, Banner, Spinner, PageHeader, ErrorNote, useAsync } from "../components/ui";

export default function ScheduleRisk() {
  const sched = useAsync<any>(() => apiGet("/schedule"));
  const sim = useAsync<any>(() => apiGet("/schedule/simulation"));

  if (sched.loading || sim.loading) return <Spinner label="Computing critical path…" />;
  if (sched.error) return <ErrorNote msg={sched.error} />;

  return (
    <div className="space-y-5">
      <PageHeader title="Predictive Schedule Risk Engine">
        Deterministic CPM (critical path in red) + LLM risk analyst. Every impact is verified by the
        what-if engine — the model never invents dates.
      </PageHeader>

      <div className="grid grid-cols-3 gap-3.5">
        <StatTile label="Forecast finish" value={sched.data.summary.project_finish} />
        <StatTile label="Duration" value={`${sched.data.summary.duration_days}d`} />
        <StatTile label="Critical tasks" value={sched.data.summary.critical_path.length} />
      </div>

      {sim.data && <SimulationClock sim={sim.data} />}

      <Gantt tasks={sched.data.tasks} start={sched.data.summary.project_start} finish={sched.data.summary.project_finish} />

      <MonteCarloPanel />

      <RiskRegister />
    </div>
  );
}

function Gantt({ tasks, start, finish }: { tasks: any[]; start: string; finish: string }) {
  const s = new Date(start).getTime();
  const span = (new Date(finish).getTime() - s) / 86400000 || 1;
  return (
    <Card title="Schedule">
      <div className="space-y-1">
        {tasks.map((t) => {
          const es = (new Date(t.early_start).getTime() - s) / 86400000;
          const w = Math.max(
            1,
            (new Date(t.early_finish).getTime() - new Date(t.early_start).getTime()) / 86400000,
          );
          return (
            <div key={t.id} className="grid grid-cols-[220px_1fr] items-center gap-2 text-[12px]">
              <span className="truncate text-mut">
                {t.wbs} {t.name}
              </span>
              <div className="relative h-[22px] overflow-hidden rounded bg-surface2">
                <div
                  className="absolute h-full rounded"
                  style={{
                    left: `${(es / span) * 100}%`,
                    width: `${(w / span) * 100}%`,
                    background: t.is_critical
                      ? "color-mix(in srgb, var(--color-crit) 72%, transparent)"
                      : "color-mix(in srgb, var(--color-accent2) 60%, transparent)",
                  }}
                />
                <span className="absolute left-2 top-0.5 z-10">
                  {t.duration_days}d{t.is_critical ? " ◆" : ""}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function SimulationClock({ sim }: { sim: any }) {
  const initIdx = useMemo(() => {
    const i = sim.weeks.findIndex((w: string) => w >= sim.today);
    return i < 0 ? sim.weeks.length - 1 : i;
  }, [sim]);
  const [idx, setIdx] = useState(initIdx);
  const wk = sim.weeks[idx];
  const h = sim.headline;

  return (
    <Card
      title="⏱ Simulation clock — early-warning replay"
      actions={<Badge tone="ok">flagged {h?.lead_weeks} weeks early</Badge>}
    >
      <p className="text-[13px] text-mut">
        Scrub the timeline. A risk turns <b className="text-warn">amber</b> when SiteMind first
        detects it and <b className="text-bad">red</b> when it bites — the gap is the lead time you
        gain.
      </p>
      <input
        type="range"
        min={0}
        max={sim.weeks.length - 1}
        value={idx}
        onChange={(e) => setIdx(Number(e.target.value))}
        className="mt-3 w-full accent-[var(--color-accent)]"
      />
      <div className="text-center font-mono text-[12px] text-mut">As of week of {wk}</div>
      <div className="mt-2 space-y-2">
        {sim.events.map((e: any) => {
          const flagged = e.detected_on <= wk;
          const bitten = e.bites_on <= wk;
          const state = !flagged ? "—" : bitten ? "BITING" : "FLAGGED (early warning)";
          const color = !flagged ? "var(--color-faint)" : bitten ? "var(--color-bad)" : "var(--color-warn)";
          const lead =
            flagged && !bitten
              ? ` · ${Math.max(0, Math.round(((new Date(e.bites_on).getTime() - new Date(wk).getTime()) / 6048e5) * 10) / 10)}w until impact`
              : "";
          return (
            <div
              key={e.ref}
              className="rounded-lg border-l-2 bg-surface2 px-3.5 py-2.5"
              style={{ borderColor: color }}
            >
              <div className="flex items-center justify-between">
                <b className="text-[13px]">{e.title}</b>
                <Badge tone={bitten ? "dev" : flagged ? "minor" : "neutral"}>{state}</Badge>
              </div>
              <div className="mt-1 text-[11px] text-faint">
                detected {e.detected_on} → bites {e.bites_on} · impact {e.impact_days ?? "—"}d{lead}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function MonteCarloPanel() {
  const { data, loading, error } = useAsync<any>(() => apiGet("/schedule/montecarlo"));
  return (
    <Card
      title="Monte Carlo finish-date forecast"
      actions={<Badge tone="neutral">probabilistic</Badge>}
    >
      <p className="text-[13px] text-mut">
        A probabilistic view distinct from the deterministic CPM finish above: each task duration is
        perturbed ±15% (triangular) over {data?.iterations ?? "500"} runs of the same CPM engine.
      </p>
      {loading && <div className="mt-3"><Spinner label="Running simulations…" /></div>}
      {error && <div className="mt-3"><Banner tone="bad">{error}</Banner></div>}
      {data && (
        <>
          <div className="mt-3 grid grid-cols-2 gap-3.5 md:grid-cols-4">
            <StatTile label="Deterministic (CPM)" value={data.deterministic_finish} />
            <StatTile label="P10 (optimistic)" value={data.p10_finish} tone="good" />
            <StatTile label="P50 (likely)" value={data.p50_finish} tone="warn" />
            <StatTile label="P90 (conservative)" value={data.p90_finish} tone="bad" />
          </div>
          <Histogram buckets={data.histogram} p50={data.p50_finish} />
        </>
      )}
    </Card>
  );
}

function Histogram({ buckets, p50 }: { buckets: any[]; p50: string }) {
  const max = Math.max(1, ...buckets.map((b) => b.count));
  return (
    <div className="mt-4">
      <div className="flex items-end gap-1.5" style={{ height: 120 }}>
        {buckets.map((b) => (
          <div key={b.days} className="flex flex-1 flex-col items-center justify-end">
            <div
              title={`${b.finish}: ${b.count} runs`}
              className="w-full rounded-t"
              style={{
                height: `${(b.count / max) * 100}%`,
                background:
                  b.finish === p50
                    ? "var(--color-warn)"
                    : "color-mix(in srgb, var(--color-accent2) 55%, transparent)",
              }}
            />
            <div className="mt-1 text-[9px] text-faint">{b.finish.slice(5)}</div>
          </div>
        ))}
      </div>
      <div className="mt-1 text-[11px] text-faint">
        Finish-week distribution across simulations (amber = P50 week).
      </div>
    </div>
  );
}

function RiskRegister() {
  const [data, setData] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function analyze() {
    setBusy(true);
    setErr(null);
    try {
      setData(await apiPost("/schedule/analyze"));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card
      title="Risk register"
      actions={
        <Button onClick={analyze} disabled={busy}>
          {busy ? "Analyzing…" : "⚡ Analyze schedule risks"}
        </Button>
      }
    >
      {busy && <Spinner label="Collecting signals, running CPM what-ifs, ranking risks…" />}
      {err && <Banner tone="bad">{err}</Banner>}
      {!data && !busy && !err && (
        <p className="text-sm text-mut">
          Run the analysis to rank risks by impact × probability, each with CPM-verified mitigations.
        </p>
      )}
      {data && !busy && (
        <div className="space-y-2.5">
          {data.risks.map((rk: any, i: number) => (
            <div
              key={i}
              className={`rounded-lg border-l-2 bg-surface2 px-3.5 py-3 ${
                rk.impact_days >= 15 ? "border-crit" : "border-warn"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <b className="text-[13.5px]">{rk.title}</b>
                <span>
                  <Badge tone={rk.impact_days >= 15 ? "major" : "minor"}>{rk.impact_days}d</Badge>{" "}
                  <span className="text-[11px] text-faint">p={rk.probability}</span>
                </span>
              </div>
              <div className="mt-1 text-[12px] text-mut">{rk.description}</div>
              <div className="mt-1 text-[11px] text-faint">
                Affected: {(rk.affected_tasks || []).join(", ") || "—"}
              </div>
              {rk.mitigations?.map((m: any, j: number) => (
                <div
                  key={j}
                  className="mt-2 rounded-lg border border-line bg-surface px-3 py-2 text-[12px]"
                >
                  <b>↳ {m.option}</b> — recovers <b>{m.schedule_recovery_days}d</b> (CPM-verified) ·{" "}
                  {m.cost_impact}
                  <div className="text-mut">{m.tradeoff}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
