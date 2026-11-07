import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { AGENTS } from "@/lib/status";
import { cn, durationMs, formatDuration } from "@/lib/utils";
import type { AgentLog } from "@/types/api";

/** Latest log per agent for a single workflow (logs are ordered by id). */
export function latestLogByAgent(logs: AgentLog[]): Record<string, AgentLog> {
  const map: Record<string, AgentLog> = {};
  for (const log of [...logs].sort((a, b) => a.id - b.id)) map[log.agent_name] = log;
  return map;
}

export function AgentProgress({ logs }: { logs: AgentLog[] }) {
  const latest = latestLogByAgent(logs);

  return (
    <ol className="grid gap-3 sm:grid-cols-3">
      {AGENTS.map((agent) => {
        const log = latest[agent.name];
        const status = log?.status ?? "PENDING";
        const Icon = status === "COMPLETED" ? CheckCircle2 : status === "FAILED" ? XCircle : status === "RUNNING" ? Loader2 : Circle;
        const color =
          status === "COMPLETED" ? "text-emerald-600" : status === "FAILED" ? "text-rose-600" : status === "RUNNING" ? "text-sky-600" : "text-slate-300";
        const border =
          status === "COMPLETED" ? "border-emerald-200 bg-emerald-50/40" : status === "FAILED" ? "border-rose-200 bg-rose-50/40" : "border-slate-200";
        return (
          <li key={agent.name} className={cn("rounded-lg border p-4", border)}>
            <div className="flex items-center gap-2">
              <Icon className={cn("h-5 w-5", color, status === "RUNNING" && "animate-spin")} />
              <p className="text-sm font-medium text-slate-900">{agent.label}</p>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {log ? `${status === "COMPLETED" ? "Completed" : status === "FAILED" ? "Failed" : "Status: " + status} · ${formatDuration(durationMs(log.started_at, log.completed_at))}` : "No execution recorded"}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
