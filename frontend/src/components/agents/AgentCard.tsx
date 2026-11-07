import { Bot } from "lucide-react";
import { Card } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { durationMs, formatDateTime, formatDuration } from "@/lib/utils";
import type { WorkspaceAgentRun } from "@/hooks/useWorkspace";

export function AgentCard({ label, description, runs }: { label: string; description: string; runs: WorkspaceAgentRun[] }) {
  const latest = runs[0]; // runs are sorted newest first
  const durations = runs.map((r) => durationMs(r.started_at, r.completed_at)).filter((d): d is number => d !== null);
  const avg = durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : null;
  const failed = runs.filter((r) => r.status === "FAILED").length;
  const succeeded = runs.filter((r) => r.status === "COMPLETED").length;

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-brand-500/10 p-2.5 text-brand-600">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">{label}</h3>
            <p className="text-xs text-slate-500">{description}</p>
          </div>
        </div>
        {latest ? <StatusBadge status={latest.status} /> : <StatusBadge status="PENDING" />}
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
        <div>
          <dt className="text-xs text-slate-500">Total runs</dt>
          <dd className="font-semibold text-slate-900">{runs.length}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Avg. execution time</dt>
          <dd className="font-semibold text-slate-900">{formatDuration(avg)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Succeeded / failed</dt>
          <dd className="font-semibold text-slate-900">
            <span className="text-emerald-600">{succeeded}</span> / <span className={failed ? "text-rose-600" : ""}>{failed}</span>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Last run</dt>
          <dd className="font-semibold text-slate-900">{latest ? formatDateTime(latest.started_at) : "—"}</dd>
        </div>
      </dl>
    </Card>
  );
}
