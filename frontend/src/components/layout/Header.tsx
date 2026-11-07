import { Menu, RefreshCw } from "lucide-react";
import { useWorkspace } from "@/hooks/useWorkspace";
import { cn } from "@/lib/utils";

export function Header({ onMenu }: { onMenu: () => void }) {
  const { refresh, refreshing, lastUpdated, status, error } = useWorkspace();
  const offline = status === "error" || (error !== null && status !== "loading");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6">
      <button
        onClick={onMenu}
        className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex items-center gap-2 text-sm text-slate-500" role="status">
        <span className={cn("h-2 w-2 rounded-full", offline ? "bg-rose-500" : status === "loading" ? "bg-slate-300" : "bg-emerald-500")} />
        <span className="hidden sm:inline">
          {offline ? "Backend unreachable" : status === "loading" ? "Connecting…" : lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Connected"}
        </span>
      </div>

      <div className="ml-auto">
        <button
          onClick={() => void refresh()}
          disabled={refreshing}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
        >
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>
    </header>
  );
}
