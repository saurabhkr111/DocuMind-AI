import { NavLink } from "react-router-dom";
import { BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav";
import { useWorkspace } from "@/hooks/useWorkspace";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { documents } = useWorkspace();
  const pending = documents.filter((d) => d.approval_status === "PENDING").length;

  return (
    <div className="flex h-full flex-col bg-navy-800 text-slate-300">
      <div className="flex h-16 items-center gap-2.5 border-b border-white/10 px-5">
        <div className="rounded-lg bg-brand-500/20 p-1.5 text-sky-300">
          <BrainCircuit className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-white">DocuMind AI</p>
          <p className="text-[11px] text-slate-400">Documentation &amp; Team Intelligence</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Main">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{label}</span>
            {to === "/approvals" && pending > 0 && (
              <span className="rounded-full bg-amber-400 px-2 py-0.5 text-[11px] font-semibold text-navy-900">{pending}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 px-5 py-3 text-xs text-slate-500">DocuMind AI Dashboard</div>
    </div>
  );
}
