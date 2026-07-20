import { useNavigate } from "react-router-dom";
import { apiGet } from "../lib/api";
import { Card, StatTile, Spinner, ErrorNote, Badge, useAsync } from "../components/ui";

export default function Dashboard() {
  const nav = useNavigate();
  const { data, loading, error } = useAsync<any>(() => apiGet("/dashboard"));

  if (loading) return <Spinner label="Loading project overview…" />;
  if (error) return <ErrorNote msg={error} />;
  const d = data;
  const healthTone = d.health_score >= 80 ? "good" : d.health_score >= 50 ? "warn" : "bad";

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight">{d.project.name}</h1>
        <p className="mt-1 text-[13.5px] text-mut">
          {d.project.description} — {d.project.tier}, {d.project.location}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3.5 md:grid-cols-3 lg:grid-cols-6">
        <StatTile label="Project health" value={d.health_score} tone={healthTone as any} />
        <StatTile label="Forecast finish" value={d.project_finish} />
        <StatTile label="Open NCRs" value={d.open_ncrs} tone={d.open_ncrs ? "warn" : "good"} />
        <StatTile label="Open risks" value={d.open_risks} tone={d.open_risks ? "warn" : "good"} />
        <StatTile
          label="At-risk shipments"
          value={d.at_risk_shipments}
          tone={d.at_risk_shipments ? "bad" : "good"}
        />
        <StatTile label="Hours saved" value={`${d.hours_saved}h`} tone="good" />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Top risks · cross-module" className="lg:col-span-2">
          {d.top_risks.length ? (
            <div className="space-y-2.5">
              {d.top_risks.map((r: any) => (
                <div
                  key={r.id}
                  className={`rounded-lg border-l-2 bg-surface2 px-3.5 py-2.5 ${
                    r.impact_days >= 15 ? "border-crit" : "border-warn"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <b className="text-[13.5px]">{r.title}</b>
                    <Badge tone={r.impact_days >= 15 ? "major" : "minor"}>{r.impact_days}d</Badge>
                  </div>
                  <div className="mt-1 text-[11.5px] text-faint">
                    {r.source_module} · probability {r.probability}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-mut">
              None yet — run a compliance check or the schedule analysis to populate the
              intelligence graph.
            </p>
          )}
        </Card>

        <Card
          title={`Document spine · ${d.documents.length}`}
          actions={
            <button
              onClick={() => nav("/audit")}
              className="rounded-md border border-line px-2.5 py-1 text-[11px] text-mut transition hover:border-line2 hover:text-ink"
            >
              {d.audit_events} audit events →
            </button>
          }
          pad={false}
        >
          <div className="max-h-80 overflow-y-auto">
            <table className="w-full text-[12.5px]">
              <tbody>
                {d.documents.slice(0, 14).map((x: any) => (
                  <tr key={x.id} className="border-b border-line/60">
                    <td className="px-4 py-1.5 font-mono text-accent">{x.id}</td>
                    <td className="px-2 py-1.5 text-faint">{x.type}</td>
                    <td className="px-2 py-1.5 text-mut">{x.title.slice(0, 34)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
