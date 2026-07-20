import { useMemo, useState } from "react";
import { apiGet } from "../lib/api";
import { Card, Spinner, PageHeader, ErrorNote, useAsync } from "../components/ui";

const GTYPES: [string, string][] = [
  ["Document", "#8a94ff"],
  ["Equipment", "#d97757"],
  ["Vendor", "#c9a94b"],
  ["Task", "#7ab8a0"],
  ["TestProcedure", "#5fa8d3"],
  ["NCR", "#e0695f"],
  ["RiskEvent", "#e05252"],
];
const COLOR = Object.fromEntries(GTYPES);

export default function Graph() {
  const { data, loading, error } = useAsync<any>(() => apiGet("/graph"));
  const [sel, setSel] = useState<string | null>(null);

  const layout = useMemo(() => {
    if (!data) return null;
    const colW = 175,
      rowH = 20,
      top = 40;
    const cols: Record<string, any[]> = {};
    GTYPES.forEach(([t]) => (cols[t] = []));
    data.nodes.forEach((n: any) => cols[n.type]?.push(n));
    const pos: Record<string, { x: number; y: number }> = {};
    let maxLen = 0;
    GTYPES.forEach(([t], ci) => {
      cols[t].forEach((n, i) => (pos[n.id] = { x: ci * colW + 90, y: top + i * rowH }));
      maxLen = Math.max(maxLen, cols[t].length);
    });
    return { pos, cols, W: GTYPES.length * colW + 60, H: top + maxLen * rowH + 20, colW, top };
  }, [data]);

  if (loading) return <Spinner label="Deriving graph…" />;
  if (error) return <ErrorNote msg={error} />;
  const L = layout!;

  const connected = new Set<string>();
  if (sel) {
    connected.add(sel);
    data.edges.forEach((e: any) => {
      if (e.source === sel || e.target === sel) {
        connected.add(e.source);
        connected.add(e.target);
      }
    });
  }
  const deg = sel ? data.edges.filter((e: any) => e.source === sel || e.target === sel).length : 0;

  return (
    <div className="space-y-4">
      <PageHeader title="Knowledge Graph">
        The relational spine as an explicit typed graph, derived at read time from the tables (
        {data.counts.nodes} nodes, {data.counts.edges} typed edges). Click any node to trace its
        relationships — e.g. Equipment → governing spec, scheduled tasks, vendor; RiskEvent →
        affected tasks. This is what makes the "one intelligence graph" literal, not a metaphor.
      </PageHeader>

      <div className="flex flex-wrap gap-3.5 text-[12px]">
        {GTYPES.map(([t, c]) => (
          <span key={t}>
            <span style={{ color: c }}>●</span> {t}
          </span>
        ))}
      </div>

      <div className="text-[12px] text-mut">
        {sel ? (
          <>
            Selected <b className="font-mono text-ink">{sel}</b> — {deg} relationship
            {deg !== 1 ? "s" : ""} highlighted.{" "}
            <button className="text-accent underline" onClick={() => setSel(null)}>
              reset
            </button>
          </>
        ) : (
          "Click a node to highlight its edges."
        )}
      </div>

      <Card pad={false}>
        <div className="max-h-[70vh] overflow-auto p-2">
          <svg viewBox={`0 0 ${L.W} ${L.H}`} width={L.W} style={{ minWidth: L.W }}>
            {GTYPES.map(([t, c], ci) => (
              <text key={t} x={ci * L.colW + 90} y={24} fill={c} fontSize={11} fontWeight={700}>
                {t} ({L.cols[t].length})
              </text>
            ))}
            {data.edges.map((e: any, i: number) => {
              const a = L.pos[e.source],
                b = L.pos[e.target];
              if (!a || !b) return null;
              const on = sel && (e.source === sel || e.target === sel);
              return (
                <line
                  key={i}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={on ? "var(--color-accent)" : "#4a4a55"}
                  strokeWidth={on ? 1.6 : 1}
                  opacity={sel ? (on ? 0.9 : 0.05) : 0.28}
                >
                  <title>{e.type}</title>
                </line>
              );
            })}
            {data.nodes.map((n: any) => {
              const p = L.pos[n.id];
              if (!p) return null;
              const dim = sel && !connected.has(n.id);
              return (
                <g
                  key={n.id}
                  style={{ cursor: "pointer", opacity: dim ? 0.25 : 1 }}
                  onClick={() => setSel(n.id)}
                >
                  <circle cx={p.x} cy={p.y} r={5} fill={COLOR[n.type]} />
                  <text x={p.x + 8} y={p.y + 3.5} fill="var(--color-mut)" fontSize={10}>
                    {n.label.slice(0, 20)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </Card>
    </div>
  );
}
