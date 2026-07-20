// Typed client for the SiteMind FastAPI backend. Uses relative /api URLs which
// Vite proxies to the backend (see vite.config.ts).

export async function apiGet<T = any>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`);
  if (!r.ok) throw new Error(await friendlyError(r));
  return r.json();
}

export async function apiPost<T = any>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(await friendlyError(r));
  return r.json();
}

async function friendlyError(r: Response): Promise<string> {
  const text = await r.text().catch(() => "");
  if (r.status === 500 && /rate.?limit|quota|429|tokens per day/i.test(text)) {
    return "Groq daily token limit reached — resets within the hour. Cached results still work.";
  }
  if (r.status === 429) return "Rate limited — please retry shortly.";
  return `Request failed (${r.status}). ${text.slice(0, 160)}`;
}

// ---- SSE streaming for the RAG chat ----
export async function askStream(
  question: string,
  onCitations: (c: Citation[]) => void,
  onToken: (t: string) => void,
): Promise<void> {
  const r = await fetch(`/api/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!r.ok || !r.body) throw new Error(await friendlyError(r));
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() || "";
    for (const p of parts) {
      const ev = /event: (.*)/.exec(p)?.[1];
      const data = /data: ([\s\S]*)/.exec(p)?.[1];
      if (!data) continue;
      if (ev === "citations") onCitations(JSON.parse(data));
      else if (ev === "token") onToken(JSON.parse(data));
    }
  }
}

// ---- shared types ----
export interface Citation {
  doc_id: string;
  title: string;
  section_ref: string | null;
  type: string;
  score: number;
}
export interface RiskEvent {
  id: string;
  source_module: string;
  title: string;
  description?: string;
  impact_days: number;
  probability: number;
  affected_tasks: string[];
  mitigation_options?: any[];
  status: string;
}
export interface Finding {
  clause_ref: string;
  requirement: string;
  submittal_value: string;
  verdict: "COMPLIANT" | "DEVIATION" | "UNCLEAR";
  severity: string;
  recommended_action: string;
}
export interface ScheduleTask {
  id: string;
  wbs: string;
  name: string;
  duration_days: number;
  early_start: string;
  early_finish: string;
  total_float: number;
  is_critical: boolean;
  spec_section?: string;
  phase?: string;
}
