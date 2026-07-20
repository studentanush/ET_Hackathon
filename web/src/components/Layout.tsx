import { NavLink, useLocation } from "react-router-dom";
import { type ReactNode, useState } from "react";
import { apiPost } from "../lib/api";
import { useToast } from "./ui";

const ICON: Record<string, ReactNode> = {
  dashboard: <path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z" />,
  compliance: <path d="M9 12l2 2 4-4M12 3l7 4v5c0 4-3 7-7 8-4-1-7-4-7-8V7z" />,
  compiler: <path d="M8 6l-4 6 4 6M16 6l4 6-4 6M13 4l-2 16" />,
  schedule: <path d="M3 6h18M3 12h18M3 18h12M17 16l2 2 3-3" />,
  supply: <path d="M3 7l9-4 9 4-9 4-9-4zM3 7v10l9 4 9-4V7M12 11v10" />,
  commissioning: <path d="M9 11l3 3 6-6M4 6h16v14H4z" />,
  knowledge: <path d="M4 5h11a3 3 0 013 3v11H7a3 3 0 01-3-3zM8 9h7M8 13h5" />,
  graph: <path d="M6 6a2 2 0 100-.01M18 6a2 2 0 100-.01M12 18a2 2 0 100-.01M7.5 7.5l3 3M16.5 7.5l-3 3M12 12v4" />,
  audit: <path d="M8 6h9M8 12h9M8 18h6M4 6h.01M4 12h.01M4 18h.01" />,
};

const NAV: [string, string, string][] = [
  ["/", "Dashboard", "dashboard"],
  ["/compliance", "Compliance", "compliance"],
  ["/spec-compiler", "Spec Compiler", "compiler"],
  ["/schedule", "Schedule Risk", "schedule"],
  ["/supply", "Supply Chain", "supply"],
  ["/commissioning", "Commissioning", "commissioning"],
  ["/knowledge", "Knowledge / RFI", "knowledge"],
  ["/graph", "Knowledge Graph", "graph"],
  ["/audit", "Audit Trail", "audit"],
];

const TITLES: Record<string, string> = Object.fromEntries(
  NAV.map(([p, label]) => [p, label]),
);

function Icon({ name }: { name: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-[18px] w-[18px] shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {ICON[name]}
    </svg>
  );
}

export default function Layout({ children, project }: { children: ReactNode; project?: any }) {
  const loc = useLocation();
  const toast = useToast();
  const [resetting, setResetting] = useState(false);
  const title = TITLES[loc.pathname] ?? "";

  async function reset() {
    setResetting(true);
    try {
      await apiPost("/reset-demo");
      toast("Demo reset to the seeded snapshot.");
      setTimeout(() => location.reload(), 400);
    } catch (e: any) {
      toast(e.message);
      setResetting(false);
    }
  }

  return (
    <div className="flex h-full">
      {/* sidebar */}
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-surface">
        <div className="flex items-center gap-2.5 px-5 py-4">
          <span className="h-2.5 w-2.5 rounded-full bg-accent shadow-[0_0_10px_var(--color-accent)]" />
          <span className="text-[17px] font-bold tracking-tight">
            <span className="text-accent">Site</span>Mind
          </span>
        </div>
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-faint">
          Modules
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-3">
          {NAV.map(([path, label, icon]) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition ${
                  isActive
                    ? "bg-surface2 text-ink shadow-[inset_0_0_0_1px_var(--color-line)]"
                    : "text-mut hover:bg-white/[.03] hover:text-ink"
                }`
              }
            >
              <Icon name={icon} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line px-4 py-3 text-[11px] text-faint">
          {project ? (
            <>
              <div className="font-medium text-mut">{project.name}</div>
              <div>{project.tier}</div>
            </>
          ) : (
            "SiteMind v0.1"
          )}
        </div>
      </aside>

      {/* main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-4 border-b border-line bg-surface px-6 py-3">
          <h2 className="text-[15px] font-semibold tracking-tight">{title}</h2>
          <div className="flex-1" />
          {project && (
            <>
              <div className="hidden text-right text-xs text-mut md:block">
                <div className="font-medium text-ink">{project.name}</div>
                <div>{project.location}</div>
              </div>
              <div className="hidden h-8 w-px bg-line md:block" />
              <div className="text-xs text-mut">Data date {project.today}</div>
            </>
          )}
          <button
            onClick={reset}
            disabled={resetting}
            className="rounded-lg border border-line bg-surface2 px-3 py-1.5 text-xs text-mut transition hover:border-line2 hover:text-ink disabled:opacity-50"
          >
            {resetting ? "Resetting…" : "↻ Reset demo"}
          </button>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto max-w-6xl animate-fade">{children}</div>
        </main>
      </div>
    </div>
  );
}
