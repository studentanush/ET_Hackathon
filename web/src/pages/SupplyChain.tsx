import { apiGet, apiPost } from "../lib/api";
import { Card, Badge, Banner, Spinner, Table, Td, PageHeader, ErrorNote, useAsync } from "../components/ui";

const W = 360,
  H = 430,
  LATMIN = 6,
  LATMAX = 37,
  LNGMIN = 67,
  LNGMAX = 98;
const px = (lat: number, lng: number) => ({
  x: ((lng - LNGMIN) / (LNGMAX - LNGMIN)) * W,
  y: H - ((lat - LATMIN) / (LATMAX - LATMIN)) * H,
});
// simplified India border (lat,lng)
const INDIA: [number, number][] = [
  [34.5, 76], [32.5, 79], [30, 81], [28.2, 88.5], [27.3, 92], [28, 95.5], [26, 97], [24, 92.5],
  [22, 89], [21.7, 87.5], [19.5, 85], [16, 82], [13.1, 80.3], [10, 79.8], [8.1, 77.5], [8.8, 76.5],
  [11, 75.2], [13, 74.6], [15, 73.8], [17.5, 73.2], [19, 72.8], [20.7, 70.9], [22.3, 69],
  [23.7, 68.2], [24.7, 71], [25.5, 70.5], [27.8, 70.2], [30, 72], [32, 74.3], [34.5, 76],
];

export default function SupplyChain() {
  const ships = useAsync<any[]>(() => apiGet("/supply/shipments"));
  const sync = useAsync<any>(() => apiPost("/supply/sync-risks"));

  if (ships.loading) return <Spinner label="Loading shipments…" />;
  if (ships.error) return <ErrorNote msg={ships.error} />;
  const rows = ships.data || [];
  const site = px(19.03, 73.02);
  const poly = INDIA.map(([la, ln]) => {
    const p = px(la, ln);
    return `${p.x.toFixed(0)},${p.y.toFixed(0)}`;
  }).join(" ");

  return (
    <div className="space-y-5">
      <PageHeader title="Supply Chain Visibility">
        Critical equipment in transit to the Navi Mumbai site. Dashed lines are delivery routes; a
        shipment is <b className="text-bad">red</b> when its ETA is later than its required-on-site
        date, <b className="text-good">green</b> when on track. At-risk items feed the Schedule Risk
        engine automatically.
      </PageHeader>

      {sync.data?.count > 0 && (
        <Banner tone="bad">
          ⚡ Cross-module: {sync.data.count} at-risk shipment
          {sync.data.count > 1 ? "s" : ""} raised a schedule risk →{" "}
          {sync.data.raised.map((r: any) => (
            <b key={r.id}>
              {r.title} ({r.impact_days}d impact){" "}
            </b>
          ))}
          . Now in Schedule Risk & Dashboard.
        </Banner>
      )}

      <div className="grid gap-5 lg:grid-cols-[400px_1fr]">
        <Card title="Shipment map · origins → site">
          <svg viewBox={`-6 -6 ${W + 80} ${H + 12}`} className="w-full">
            <polygon points={poly} fill="#232329" stroke="#3a3a42" strokeWidth={1.2} />
            {rows.map((s) => {
              const o = px(s.current_lat, s.current_lng);
              return (
                <line
                  key={"l" + s.id}
                  x1={o.x}
                  y1={o.y}
                  x2={site.x}
                  y2={site.y}
                  stroke={s.at_risk ? "var(--color-bad)" : "var(--color-accent2)"}
                  strokeWidth={1.3}
                  strokeDasharray="4 3"
                  opacity={0.5}
                />
              );
            })}
            {rows.map((s) => {
              const p = px(s.current_lat, s.current_lng);
              return (
                <g key={s.id}>
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={7}
                    fill={s.at_risk ? "var(--color-bad)" : "var(--color-good)"}
                    stroke="var(--color-bg)"
                    strokeWidth={2}
                  >
                    <title>{`${s.description} — from ${s.origin}, ${s.status}`}</title>
                  </circle>
                  <text x={p.x + 10} y={p.y + 4} fill="var(--color-mut)" fontSize={10}>
                    {(s.origin || "").split(",")[0]}
                  </text>
                </g>
              );
            })}
            <polygon
              points={`${site.x},${site.y - 9} ${site.x + 8},${site.y} ${site.x},${site.y + 9} ${
                site.x - 8
              },${site.y}`}
              fill="var(--color-accent)"
            />
            <text x={site.x + 11} y={site.y + 4} fill="var(--color-accent)" fontSize={10} fontWeight={600}>
              Site (Navi Mumbai)
            </text>
          </svg>
          <div className="mt-2 flex gap-4 text-[12px]">
            <span>
              <span className="text-good">●</span> on-track
            </span>
            <span>
              <span className="text-bad">●</span> at-risk
            </span>
            <span>
              <span className="text-accent">◆</span> project site
            </span>
          </div>
        </Card>

        <Card title="Tracked shipments" pad={false}>
          <Table head={["Equipment", "Origin", "ETA", "Required", "Status"]}>
            {rows.map((s) => (
              <tr key={s.id}>
                <Td>
                  {s.description}
                  <div className="text-[11px] text-faint">{s.tier_supplier}</div>
                </Td>
                <Td>{(s.origin || "").split(",")[0]}</Td>
                <Td>{s.eta}</Td>
                <Td>{s.required_on_site}</Td>
                <Td>
                  <Badge tone={s.at_risk ? "dev" : "ok"}>{s.status}</Badge>
                </Td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </div>
  );
}
