import { Link } from "react-router-dom";
import { StatusBadge } from "@/components/common/StatusBadge";
import { agentLabel } from "@/lib/status";
import { durationMs, formatDateTime, formatDuration } from "@/lib/utils";
import type { WorkspaceAgentRun } from "@/hooks/useWorkspace";

export function AgentRunsTable({ runs }: { runs: WorkspaceAgentRun[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-5 py-3 font-medium">Agent</th>
            <th className="px-5 py-3 font-medium">Workflow</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="px-5 py-3 font-medium">Started</th>
            <th className="px-5 py-3 font-medium">Execution time</th>
            <th className="px-5 py-3 font-medium">Error</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {runs.map((r) => (
            <tr key={r.id}>
              <td className="whitespace-nowrap px-5 py-3 font-medium text-slate-900">{agentLabel(r.agent_name)}</td>
              <td className="max-w-[14rem] px-5 py-3">
                <Link to={`/workflows/${r.workflow_id}`} className="line-clamp-1 text-brand-600 hover:text-brand-700">
                  #{r.workflow_id} · {r.workflow_title}
                </Link>
              </td>
              <td className="px-5 py-3">
                <StatusBadge status={r.status} />
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">{formatDateTime(r.started_at)}</td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">{formatDuration(durationMs(r.started_at, r.completed_at))}</td>
              <td className="max-w-xs px-5 py-3 text-rose-700">
                <span className="line-clamp-2 break-words" title={r.error_message ?? undefined}>
                  {r.error_message ?? <span className="text-slate-300">—</span>}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
