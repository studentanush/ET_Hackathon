import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

// ---------------------------------------------------------------- data hook
export function useAsync<T>(fn: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useCallback(() => {
    setLoading(true);
    setError(null);
    fn()
      .then((d) => setData(d))
      .catch((e) => setError(e.message || String(e)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(run, [run]);
  return { data, error, loading, reload: run };
}

// ---------------------------------------------------------------- primitives
export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-mut text-sm">
      <span
        className="inline-block h-4 w-4 rounded-full border-2 border-line2 border-t-accent"
        style={{ animation: "spin .8s linear infinite" }}
      />
      {label}
    </span>
  );
}

export function Card({
  children,
  className = "",
  title,
  actions,
  pad = true,
}: {
  children: ReactNode;
  className?: string;
  title?: ReactNode;
  actions?: ReactNode;
  pad?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(0,0,0,.4),0_10px_30px_rgba(0,0,0,.15)] ${className}`}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h3 className="text-[15px] font-semibold tracking-tight">{title}</h3>
          {actions}
        </div>
      )}
      <div className={pad ? "p-4" : ""}>{children}</div>
    </div>
  );
}

type Tone = "good" | "warn" | "bad" | "neutral" | "info";
const toneText: Record<Tone, string> = {
  good: "text-good",
  warn: "text-warn",
  bad: "text-bad",
  neutral: "text-ink",
  info: "text-info",
};

export function StatTile({
  label,
  value,
  tone = "neutral",
  sub,
  onClick,
}: {
  label: string;
  value: ReactNode;
  tone?: Tone;
  sub?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`rounded-xl border border-line bg-surface p-4 ${
        onClick ? "cursor-pointer transition hover:border-line2" : ""
      }`}
    >
      <div className={`text-[26px] font-bold leading-none tracking-tight ${toneText[tone]}`}>
        {value}
      </div>
      <div className="mt-2 text-[11px] font-medium uppercase tracking-wider text-mut">
        {label}
      </div>
      {sub && <div className="mt-0.5 text-[11px] text-faint">{sub}</div>}
    </div>
  );
}

const badgeTone: Record<string, string> = {
  good: "bg-good/15 text-good",
  ok: "bg-good/15 text-good",
  warn: "bg-warn/15 text-warn",
  minor: "bg-warn/20 text-warn",
  bad: "bg-bad/15 text-bad",
  dev: "bg-bad/15 text-bad",
  major: "bg-bad/20 text-bad",
  crit: "bg-crit text-white",
  critical: "bg-crit text-white",
  neutral: "bg-surface2 text-mut",
};
export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  return (
    <span
      className={`inline-block rounded-md px-2 py-0.5 text-[11px] font-semibold tracking-wide ${
        badgeTone[tone] || badgeTone.neutral
      }`}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost";
  disabled?: boolean;
  className?: string;
}) {
  const base =
    "rounded-lg px-4 py-2 text-[13px] font-semibold transition disabled:opacity-50 disabled:cursor-wait";
  const styles =
    variant === "primary"
      ? "bg-accent text-[#1a1108] hover:brightness-110"
      : "border border-accent/45 text-accent hover:bg-accent/10";
  return (
    <button className={`${base} ${styles} ${className}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

export function Banner({ tone = "info", children }: { tone?: "good" | "bad" | "info"; children: ReactNode }) {
  const map = {
    good: "border-good/40 bg-good/10 text-good",
    bad: "border-crit/45 bg-crit/10 text-[#f2c4c1]",
    info: "border-info/40 bg-info/10 text-info",
  };
  return (
    <div className={`rounded-lg border px-4 py-3 text-[13px] font-medium ${map[tone]}`}>
      {children}
    </div>
  );
}

export function Table({ head, children }: { head: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr>
            {head.map((h) => (
              <th
                key={h}
                className="border-b border-line px-3 py-2 text-left text-[10.5px] font-semibold uppercase tracking-wide text-mut"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
export function Td({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return <td className={`border-b border-line/60 px-3 py-2 align-top ${className}`}>{children}</td>;
}

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="mb-5">
      <h1 className="text-[22px] font-semibold tracking-tight">{title}</h1>
      {children && <p className="mt-1 max-w-3xl text-[13.5px] leading-relaxed text-mut">{children}</p>}
    </div>
  );
}

export function ErrorNote({ msg }: { msg: string }) {
  return <Banner tone="bad">{msg}</Banner>;
}

// -------------------------------------------------- lightweight toast context
const ToastCtx = createContext<(m: string) => void>(() => {});
export const useToast = () => useContext(ToastCtx);
export function ToastHost({ children }: { children: ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const push = useCallback((m: string) => {
    setMsg(m);
    setTimeout(() => setMsg(null), 3200);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      {msg && (
        <div className="fixed bottom-5 right-5 z-50 animate-fade rounded-lg border border-line2 bg-surface2 px-4 py-3 text-sm shadow-xl">
          {msg}
        </div>
      )}
    </ToastCtx.Provider>
  );
}
