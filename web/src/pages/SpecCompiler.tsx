import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { Card, Button, Badge, Banner, Spinner, Table, Td, PageHeader } from "../components/ui";

export default function SpecCompiler() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // pre-fill the textarea with the demo fixture on mount
  useEffect(() => {
    apiGet("/spec-compiler/demo-fixture")
      .then((d) => setText(d.raw_text))
      .catch(() => {});
  }, []);

  async function loadDemo() {
    const d = await apiGet("/spec-compiler/demo-fixture");
    setText(d.raw_text);
    setResult(null);
    setErr(null);
  }

  async function compile() {
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      setResult(await apiPost("/spec-compiler/compile", { raw_text: text }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Spec → Rule Compiler">
        Paste a specification section written as normal prose. The agent compiles it into the same
        machine-checkable clause schema the compliance engine uses ({"{"}ref, param, op, value,
        severity{"}"}) — turning unstructured spec language into rules a machine can enforce. This
        is a live LLM call and runs independently of the seeded specs.
      </PageHeader>

      <Card
        title="Specification text"
        actions={
          <Button variant="ghost" onClick={loadDemo}>
            Load demo spec
          </Button>
        }
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
          className="h-64 w-full rounded-lg border border-line bg-surface2 px-3 py-2 font-mono text-[12.5px] leading-relaxed outline-none focus:border-accent"
          placeholder="Paste a spec section here…"
        />
        <div className="mt-3 flex items-center gap-3">
          <Button onClick={compile} disabled={busy || !text.trim()}>
            {busy ? "Compiling…" : "Compile to rules"}
          </Button>
          {busy && <Spinner label="Extracting requirements (live LLM)…" />}
        </div>
      </Card>

      {err && <Banner tone="bad">{err}</Banner>}

      {result && (
        <Card
          title={`Compiled rules · ${result.section} ${result.title}`}
          actions={<Badge tone="ok">{result.clauses.length} clauses</Badge>}
          pad={false}
        >
          <div className="p-4">
            <Table head={["Ref", "Parameter", "Op", "Value", "Unit", "Severity", "Requirement"]}>
              {result.clauses.map((c: any, i: number) => (
                <tr key={i}>
                  <Td className="font-mono">{c.ref}</Td>
                  <Td className="font-mono text-accent">{c.param}</Td>
                  <Td className="font-mono">{c.op}</Td>
                  <Td>{c.value}</Td>
                  <Td className="text-mut">{c.unit || "—"}</Td>
                  <Td>
                    <Badge tone={c.severity}>{c.severity}</Badge>
                  </Td>
                  <Td className="text-mut">{c.text}</Td>
                </tr>
              ))}
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}
