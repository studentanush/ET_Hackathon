import { apiGet } from "../lib/api";
import { Card, Badge, Spinner, Table, Td, PageHeader, ErrorNote, useAsync } from "../components/ui";

export default function Audit() {
  const { data, loading, error } = useAsync<any[]>(() => apiGet("/audit"));
  if (loading) return <Spinner label="Loading audit trail…" />;
  if (error) return <ErrorNote msg={error} />;
  const rows = data || [];

  const detail = (d: any) =>
    d && typeof d === "object"
      ? Object.entries(d)
          .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : v}`)
          .join(", ")
      : "";

  return (
    <div className="space-y-5">
      <PageHeader title="Audit Trail">
        Every write to the data spine — compliance verdicts, NCRs, commissioning validations — is
        recorded in reverse-chronological order for QMS traceability. {rows.length} event
        {rows.length !== 1 ? "s" : ""}.
      </PageHeader>
      <Card pad={false}>
        {rows.length ? (
          <Table head={["When", "Actor", "Action", "Entity", "ID", "Detail"]}>
            {rows.map((r, i) => (
              <tr key={i}>
                <Td className="whitespace-nowrap font-mono text-mut">
                  {new Date(r.at).toLocaleString()}
                </Td>
                <Td>{r.actor}</Td>
                <Td>
                  <Badge tone={r.action === "create" ? "minor" : "ok"}>{r.action}</Badge>
                </Td>
                <Td>{r.entity}</Td>
                <Td className="font-mono">{r.entity_id}</Td>
                <Td className="text-mut">{detail(r.detail).slice(0, 90)}</Td>
              </tr>
            ))}
          </Table>
        ) : (
          <p className="p-4 text-sm text-mut">
            No events yet. Run a compliance check or a commissioning validation to populate the
            trail.
          </p>
        )}
      </Card>
    </div>
  );
}
